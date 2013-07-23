using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Web;
using System.Xml.Linq;

/// <summary>
/// Класс определения поисковиков и ботов по user-agent
/// </summary>

public class CheckUserAgent
{
    private HashSet<string> UserAgentList = new HashSet<string>();
    protected CheckUserAgent()
    {
        LoadBotFile();
    }

    private sealed class CreatorCheckUserAgent
    {
        private static readonly CheckUserAgent instance = new CheckUserAgent();
        public static CheckUserAgent Instance { get { return instance; } }
    }

    public static CheckUserAgent Instance
    {
        get { return CreatorCheckUserAgent.Instance; }
    }

    /// <summary>
    /// 
    /// </summary>
    /// <param name="file"></param>
    /// <returns></returns>
    public static CheckUserAgent New(string file)
    {
        BotFile = file;
        return CreatorCheckUserAgent.Instance;
    }

    private static string _botFile;                     // Файл со списком user-agent'ов
    private static string _loadedBotFile;               // Имя реально загруженного файла
    public static string BotFile
    {
        get
        {
            return string.IsNullOrEmpty(_botFile) ? "allagents.xml" : _botFile;
        }
        set
        {
                _botFile = value;
        }
    }

    private System.Threading.Mutex _mutex = new System.Threading.Mutex();
    private void LoadBotFile()
    {
        try
        {
            if (!_mutex.WaitOne(0))
                return;

            UserAgentList.Clear();
            if (string.IsNullOrEmpty(BotFile))
                return;

            XDocument doc = XDocument.Load(BotFile);
            foreach (XElement el in doc.Root.Elements())
            {
                foreach (XElement ex in el.Elements())
                {
                    if (ex.Name == "String")
                        UserAgentList.Add(ex.Value);
                }
            }
            _loadedBotFile = BotFile;
        }
        catch { }
        finally
        {
            _mutex.ReleaseMutex();
        }
    }

    public bool IsBot(string userAgent)
    {
        if (_loadedBotFile != _botFile)
            LoadBotFile();
        return UserAgentList.Contains(userAgent);
    }

}

