using System;
using System.Collections.Generic;
using System.Configuration;
using System.Web;
using System.Data.SqlClient;
using System.Web.Configuration;


public class Db
{
    public enum ConnectionStrings
    {
        Rynok,
        Adload,
        Stats,
        GetMyAd
    }

    /// <summary>
    /// Возвращает заданную строку подключения
    /// </summary>
    /// <returns></returns>
    public static string ConnectionString(Db.ConnectionStrings connectionStringType)
    {
        string s;
        switch (connectionStringType)
        {
            case ConnectionStrings.Rynok:
                s = "RynokConnectionString";
                break;
            case ConnectionStrings.Adload:
                s = "AdloadConnectionString";
                break;
            case ConnectionStrings.Stats:
                s = "StatisticConnectionString";
                break;
            case ConnectionStrings.GetMyAd:
                s = "GetMyAdConnectionString";
                break;
            default:
                throw new Exception("Неизвестный тип строки подключения!");
        }
        ConnectionStringsSection connectionStringsSection = ((ConnectionStringsSection)(WebConfigurationManager.GetSection("connectionStrings")));
        return connectionStringsSection.ConnectionStrings[s].ToString();
    }


    /// <summary>
    /// Выполняет запрос sql с параметрами parameters (Имя_параметра => Значение)
    /// </summary>
    /// <param name="sql"></param>
    /// <param name="parameters"></param>
    /// <param name="database"></param>
    /// <returns></returns>
    public static object ExecuteScalar(string sql, Dictionary<string, object> parameters, ConnectionStrings database, bool storedProcedure)
    {
        try
        {
            using (SqlConnection connection = new SqlConnection(ConnectionString(database)))
            {
                connection.Open();
                SqlCommand cmd = new SqlCommand(sql, connection);
                if (storedProcedure) cmd.CommandType = System.Data.CommandType.StoredProcedure;
                foreach (KeyValuePair<string, object> p in parameters)
                    cmd.Parameters.AddWithValue(p.Key, p.Value);
                return cmd.ExecuteScalar();
            }
        }
        catch (Exception ex)
        {
            Common.Log(ex);
            return null;
        }
    }

}
