using System;
using System.Collections;
using System.Collections.Generic;
using System.Net.Sockets;
using UnityEngine;

public class NPCClient : MonoBehaviour
{
    public enum TextToSpeechModels
    {
        [InspectorName("Facebook TTS Model")]Local_TTS,
        [InspectorName("Amazon Polly Model")]Amazon_polly,
        [InspectorName("OpenAI TTS Model")]OpenAI_tts
    }
    public TextToSpeechModels TTSModel = TextToSpeechModels.OpenAI_tts;

    private string OpenAIVoice = "alloy";

    public enum LLMModels
    {
        [InspectorName("Base Model")]Local_base,
        [InspectorName("OpenAI GPT 3.5 Model")]OpenAI_gpt3_5_turbo,
        [InspectorName("OpenAI GPT 3.5 Model with Streaming mode")]OpenAI_gpt3_5_turbo_stream,
        [InspectorName("OpenAI GPT 4 Model")]OpenAI_gpt4_turbo,
        [InspectorName("OpenAI GPT 4 Model with Streaming mode")]OpenAI_gpt4_turbo_stream,
        [InspectorName("OpenAI GPT 4o Model")]OpenAI_gpt4o,
        [InspectorName("OpenAI GPT 4o Model with Streaming mode")]OpenAI_gpt4o_stream,
        [InspectorName("OpenAI GPT 4o-mini Model")]OpenAI_gpt4o_mini,
        [InspectorName("OpenAI GPT 4o-mini Model with Streaming mode")]OpenAI_gpt4o_mini_stream,
        [InspectorName("OpenAI Gemini Model")]Google_gemini,
        [InspectorName("HuggingFace Custom Model")]HuggingFace
    }
    public LLMModels LLM = LLMModels.OpenAI_gpt4o_mini_stream;
    public enum SpeechToTextModels
    {
        [InspectorName("Facebook STT Model")]Local_STT,
        [InspectorName("OpenAI Whisper Model")]OpenAI_whisper,
        [InspectorName("Amazon Transcribe Model")]Amazon_transcribe
    }
    public SpeechToTextModels STTModel = SpeechToTextModels.OpenAI_whisper;
    public string CustomLLM = "";
    [TextArea(5,15)]public string systemPrompt = ""; // TextArea(minArea, maxArea) areas that shown on the inspector

    [Header("Server Settings")] // Header for grouping variables in the inspector
    public string serverIP = "127.0.0.1";
    public int serverPort = 9999;

    [Header("OpenAI")] // Header for grouping variables in the inspector
    public string SecretAPIKey = "";

    [Header("Amazon")] // Header for grouping variables in the inspector
    public string AccessKeyID = "";
    public string SecretKey = "";

    [Header("Google")] // Header for grouping variables in the inspector
    public string APIKey = "";

    [Header("Other Settings")] // Header for grouping variables in the inspector

    public bool storeHistory = true;

    public int recordTime = 10; // Record time in seconds
    
    private bool isRecording = false;
    private AudioClip recordedClip;
    private TcpClient client;
    private NetworkStream stream;

    private byte[] lengthDataReceived = new byte[4];
    private int expectedDataLength = -1;
    private byte[] receivedData;
    private int totalBytesRead = 0;
    private bool connectionEstablished = false;
    private IEnumerator coroutine;
    private float lastSentTime;
    private AudioSource audioSource;
    int lastPartFlag = 0;
    private Queue<AudioClip> audioQueue = new Queue<AudioClip>(); // Queue to hold audio clips


    // Start is called before the first frame update
    void Start()
    {
        StartSocketConnection();
        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space) && connectionEstablished)
        {
            if (!isRecording)
            {
                StartRecording();
            }
            else
            {
                StopRecording();
                SendReceiveRecordedAudio();
            }
        }
        if (!audioSource.isPlaying && audioQueue.Count > 0)
        {
            AudioClip clip = audioQueue.Dequeue();
            audioSource.PlayOneShot(clip);
        }
    }

    void StartSocketConnection()
    {
        try
        {
            client = new TcpClient(serverIP, serverPort);
            stream = client.GetStream();
            Debug.Log("Connected to Python server.");
            string message = "";
            if (LLM == LLMModels.HuggingFace)
                message = STTModel + "," + "HuggingFace_" + CustomLLM + "," + TTSModel;
            else
                message = STTModel + "," + LLM + "," + TTSModel;
            message += "," + SecretAPIKey + "," + AccessKeyID + "," + SecretKey + "," + APIKey;
            if (storeHistory)
                message += "," + "store";
            else
                message += "," + "nostore";
            message += "," + OpenAIVoice;
            message += "," + systemPrompt;
            byte[] messageData = System.Text.Encoding.ASCII.GetBytes(message);
            byte[] lengthData = BitConverter.GetBytes(messageData.Length);
            byte[] bytesDataWithLength = new byte[messageData.Length + lengthData.Length];
            lengthData.CopyTo(bytesDataWithLength, 0);
            messageData.CopyTo(bytesDataWithLength, lengthData.Length);
            stream.Write(bytesDataWithLength, 0, bytesDataWithLength.Length);
            Debug.Log("Message" + message + " sent to Python server.");
            Debug.Log("Save path: " + Application.persistentDataPath);
            InvokeRepeating("checkConnection", 0.1f, 0.1f);
        }
        catch (SocketException e)
        {
            Debug.Log("SocketException: " + e);
        }
    }

    void checkConnection()
    {
        byte [] buffer = new byte[3];
        if(stream.DataAvailable && stream.Read(buffer, 0, buffer.Length) == buffer.Length)
        {
            string response = System.Text.Encoding.ASCII.GetString(buffer);
            if(response == "!OK")
            {
                connectionEstablished = true;
                Debug.Log("Connection established with Python server.");
                CancelInvoke("checkConnection");
            }
            else
            {
                Debug.Log("Connection failed with Python server.");
                CancelInvoke("checkConnection");
            }
        }
    }

    /*async*/ void StartRecording()
    {
        isRecording = true;
        recordedClip = Microphone.Start(null, true, recordTime, 44100);
        coroutine = sendRecordingPart();
        StartCoroutine(coroutine);
        // Debug.Log("Recording started.");
    }

    IEnumerator sendRecordingPart()
    {
        int partNumber = 1;
        while(true)
        {
            yield return new WaitForSeconds(recordTime);
            string partFile = "Assets/recorded" + partNumber + ".wav";
            SavWav.Save(partFile, recordedClip);
            lastSentTime = Time.time;
            string filePath = Application.persistentDataPath + "/" + partFile;
            byte[] bytesData = System.IO.File.ReadAllBytes(filePath);
            Debug.Log("Audio data length: " + bytesData.Length + " bytes.");
            byte[] lengthData = new byte[4];
            lengthData = BitConverter.GetBytes(bytesData.Length);
            // finished flag 1 if recording is finished 0 if not
            byte[] finishedFlag = new byte[1] {0};
            byte[] bytesDataWithLength = new byte[bytesData.Length + lengthData.Length + 1];
            lengthData.CopyTo(bytesDataWithLength, 0);
            finishedFlag.CopyTo(bytesDataWithLength, lengthData.Length);
            bytesData.CopyTo(bytesDataWithLength, lengthData.Length+1);
            // Debug.Log("Audio data length: " + lengthData + " bytes." + " with length: " + BitConverter.ToInt32(lengthData, 0) + " bytes.");
            // Debug.Log("Audio data length with length: " + bytesDataWithLength.Length + " bytes.");
            stream.Write(bytesDataWithLength, 0, bytesDataWithLength.Length);
            Debug.Log("Audio data sent to Python server.");
        }
    }

    /*async*/ void StopRecording()
    {
        Microphone.End(null);
        StopCoroutine(coroutine);
        isRecording = false;
        string partFile = "Assets/recorded0.wav";
        var samples = new float[recordedClip.samples];
        int alreadySent = (int)((recordTime - (Time.time - lastSentTime)) * recordedClip.frequency * recordedClip.channels);
        // Debug.Log("Already sent: " + alreadySent + " samples. recording length: " + recordedClip.samples + " samples.");
        // Debug.Log("Time: " + Time.time + " lastSentTime: " + lastSentTime);
		recordedClip.GetData(samples, 0);
        for (int i = 0; i < alreadySent; i++)
        {
            samples[recordedClip.samples-i-1] = 0;
        }
        recordedClip = AudioClip.Create("trimmed", recordedClip.samples, recordedClip.channels, recordedClip.frequency, false);
        recordedClip.SetData(samples, 0);
        SavWav.Save(partFile, recordedClip);
        string filePath = Application.persistentDataPath + "/" + partFile;
        byte[] bytesData = System.IO.File.ReadAllBytes(filePath);
        // Debug.Log("Audio data length: " + bytesData.Length + " bytes.");
        byte[] lengthData = new byte[4];
        lengthData = BitConverter.GetBytes(bytesData.Length);
        byte[] finishedFlag = new byte[1] {1};
        byte[] bytesDataWithLength = new byte[bytesData.Length + lengthData.Length + 1];
        lengthData.CopyTo(bytesDataWithLength, 0);
        finishedFlag.CopyTo(bytesDataWithLength, lengthData.Length);
        bytesData.CopyTo(bytesDataWithLength, lengthData.Length+1);
        // Debug.Log("Audio data length: " + lengthData + " bytes." + " with length: " + BitConverter.ToInt32(lengthData, 0) + " bytes.");
        // Debug.Log("Audio data length with length: " + bytesDataWithLength.Length + " bytes.");
        stream.Write(bytesDataWithLength, 0, bytesDataWithLength.Length);
        Debug.Log("Audio data sent to Python server.");
    }

    private float[] ConvertByteToFloat(byte[] array) 
    {
        float[] floatArr = new float[array.Length / 4];
        for (int i = 0; i < floatArr.Length; i++) 
        {
            if (BitConverter.IsLittleEndian) 
                Array.Reverse(array, i * 4, 4);
            floatArr[i] = BitConverter.ToSingle(array, i * 4);
        }
        return floatArr;
    } 

    void SendReceiveRecordedAudio()
    {
        if (LLM.ToString().Contains("_stream"))
        {
            InvokeRepeating("ReceiveDataParts", 0.1f, 0.01f); // Adjust the repeat rate as needed
        }else 
        {
            InvokeRepeating("ReceiveData", 0.1f, 0.01f); // Adjust the repeat rate as needed
        }
    }

    void ReceiveData()
    {
        if(expectedDataLength == -1) // Check if we are waiting for the length info
        {
            if(stream.DataAvailable && stream.Read(lengthDataReceived, 0, lengthDataReceived.Length) == lengthDataReceived.Length)
            {
                expectedDataLength = BitConverter.ToInt32(lengthDataReceived, 0);
                receivedData = new byte[expectedDataLength];
                // Debug.Log("Expected audio data length: " + expectedDataLength + " bytes.");
            }
        }
        else // We are receiving the actual data
        {
            if(stream.DataAvailable)
            {
                int bytesRead = stream.Read(receivedData, totalBytesRead, expectedDataLength - totalBytesRead);
                totalBytesRead += bytesRead;

                if(totalBytesRead >= expectedDataLength) // Check if all data is received
                {
                    Debug.Log("All audio data received.");
                    ProcessReceivedData(); // Process the received audio data
                    expectedDataLength = -1; // Reset the expected data length
                    totalBytesRead = 0; // Reset the total bytes read
                    receivedData = null; // Reset the received data
                    lengthDataReceived = new byte[4]; // Reset the length data received
                    CancelInvoke("ReceiveData"); // Stop invoking this method
                }
            }
        }
    }

    void ReceiveDataParts()
    {
        if(expectedDataLength == -1) // Check if we are waiting for the length info
        {
            if(stream.DataAvailable && stream.Read(lengthDataReceived, 0, lengthDataReceived.Length) == lengthDataReceived.Length)
            {
                expectedDataLength = BitConverter.ToInt32(lengthDataReceived, 0);
                receivedData = new byte[expectedDataLength];
                // Debug.Log("Expected audio data length: " + expectedDataLength + " bytes.");
                lastPartFlag = stream.ReadByte();
                // Debug.Log("Last part flag: " + lastPartFlag);
            }
        }
        else // We are receiving the actual data
        {
            if(stream.DataAvailable)
            {
                int bytesRead = stream.Read(receivedData, totalBytesRead, expectedDataLength - totalBytesRead);
                totalBytesRead += bytesRead;

                if(totalBytesRead >= expectedDataLength) // Check if all data is received
                {
                    if(lastPartFlag == 1)
                    {
                        if(expectedDataLength != 0){
                            Debug.Log("All audio data received for streaming.");
                            ProcessReceivedData(); // Process the received audio data
                        }
                        Debug.Log("Finish audio data received for streaming.");
                        expectedDataLength = -1; // Reset the expected data length
                        totalBytesRead = 0; // Reset the total bytes read
                        receivedData = null; // Reset the received data
                        lengthDataReceived = new byte[4]; // Reset the length data received
                        lastPartFlag = 0;
                        CancelInvoke("ReceiveDataParts"); // Stop invoking this method    
                    }
                    else
                    {
                        Debug.Log("Part of audio data received for streaming.");
                        ProcessReceivedData(); // Process the received audio data
                        expectedDataLength = -1; // Reset the expected data length
                        totalBytesRead = 0; // Reset the total bytes read
                        receivedData = null; // Reset the received data
                        lastPartFlag = 0;
                        lengthDataReceived = new byte[4]; // Reset the length data received
                    }             
                }
            }else if(lastPartFlag == 1)
            {
                Debug.Log("Finish audio data received for streaming without audio.");
                expectedDataLength = -1; // Reset the expected data length
                totalBytesRead = 0; // Reset the total bytes read
                receivedData = null; // Reset the received data
                lengthDataReceived = new byte[4]; // Reset the length data received
                lastPartFlag = 0;
                CancelInvoke("ReceiveDataParts"); // Stop invoking this method    
            }
        }
    }

    void ProcessReceivedData()
    {
        // Process your received data here (e.g., save to file, convert to AudioClip, etc.)
        string receivedFilePath = Application.persistentDataPath + "/Assets/received.wav";
        System.IO.File.WriteAllBytes(receivedFilePath, receivedData);
        // Debug.Log("Audio data saved to file: " + receivedFilePath);

        // Example of playing the received audio
        AudioClip receivedClip = WavUtility.ToAudioClip(receivedFilePath);
        // receivedClip = SavWav.TrimSilence(receivedClip, 0.001f);
        // audioSource.clip = receivedClip;
        // audioSource.Play();
        audioQueue.Enqueue(receivedClip);
        Debug.Log("Received audio data processed and played.");
    }
}
