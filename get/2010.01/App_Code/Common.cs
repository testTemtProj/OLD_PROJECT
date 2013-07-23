using System;
using System.Collections.Generic;
using System.Web;
using System.IO;

public class Common
{

    public static string LogName = "log.txt";
    /// <summary>
    /// Записывает в лог сообщение об исключении ex
    /// </summary>
    /// <param name="ex"></param>
    public static void Log(Exception ex)
    {
        Log(ex.Message);
    }


    /// <summary>
    /// Записывает в лог сообщение message и информацию об исключении ex
    /// </summary>
    /// <param name="ex"></param>
    /// <param name="message"></param>
    public static void Log(Exception ex, string message)
    {
        Log("\n" + ex.Message + "\n" + message + "\n");
    }


    /// <summary>
    /// Записывает в лог сообщение message
    /// </summary>
    /// <param name="message"></param>
    public static void Log(string message)
    {
        try
        {
            string logPath = HttpContext.Current.Server.MapPath("log");
            StreamWriter stream = new StreamWriter(logPath + "\\" + LogName, true);
            stream.WriteLine(DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "\t" + message);
            stream.Close();
        }
        catch (Exception)
        {
        }
    }



}

