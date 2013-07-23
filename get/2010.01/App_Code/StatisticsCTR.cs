using System;
using System.Collections.Generic;
using System.Web;
using System.Data.SqlClient;
using System.Web.Configuration;
using System.Configuration;

/// <summary>
/// Summary description for StatisticsCTR
/// </summary>
public class StatisticsCTR
{
    public StatisticsCTR()
    {
    }


    /// <summary>
    /// Делает отметку о показе товара LotID в рекламном скрипте AdvertiseScriptID
    /// </summary>
    /// <param name="LotID"></param>
    /// <param name="AdvertiseScriptID"></param>
    /// <param name="ip"></param>
    public static void ItemImpressed(Guid LotID, Guid AdvertiseScriptID, string ip)
    {
        AddAction(LotID, AdvertiseScriptID, ip, ActionType.Impression);
    }


    /// <summary>
    /// Делает отметку о переходе на товар LotID через рекламный скрипт AdvertiseScriptID
    /// </summary>
    /// <param name="LotID"></param>
    /// <param name="AdvertiseScriptID"></param>
    /// <param name="ip"></param>
    public static void ItemClicked(Guid LotID, Guid AdvertiseScriptID, string ip, string Token, string UserAgent)
    {
        AddAction(LotID, AdvertiseScriptID, ip, ActionType.Clicked);
        AddGetMyAdClick(LotID, AdvertiseScriptID, ip, Token, UserAgent);
    }




    /// <summary>
    /// Пересчитывает статистику по скрипту ScriptID по состоянию на данный момент
    /// </summary>
    public static void UpdateStatistics(Guid ScriptID)
    {
        Db.ExecuteScalar("update_st_AdCTR", new Dictionary<string, object>(), Db.ConnectionStrings.Stats, true);
    }






    enum ActionType
    {
        Impression = 0,
        Clicked = 1
    };

    private static void AddAction(Guid LotID, Guid AdvertiseScriptID, string ip, ActionType action)
    {
        using (SqlConnection connection = new SqlConnection(Db.ConnectionString(Db.ConnectionStrings.Stats)))
        {
            connection.Open();
            SqlCommand cmd = new SqlCommand("s_StatisticAds_add", connection);
            cmd.CommandType = System.Data.CommandType.StoredProcedure;
            cmd.Parameters.AddWithValue("@IP", ip);
            cmd.Parameters.AddWithValue("@ScriptID", AdvertiseScriptID);
            cmd.Parameters.AddWithValue("@LotID", LotID);
            cmd.Parameters.AddWithValue("@Action", (action == ActionType.Clicked) ? 1 : 0);
            try
            {
                cmd.ExecuteNonQuery();
            }
            catch (Exception e1)
            {
                Common.Log(e1);
            }
            finally
            {
                if ((connection != null) && (connection.State != System.Data.ConnectionState.Closed))
                    connection.Close();
            }
        }
    }


    private static void AddGetMyAdClick(Guid LotID, Guid ScriptID, string ip, string Token, string UserAgent)
    {
        using (SqlConnection connection = new SqlConnection(Db.ConnectionString(Db.ConnectionStrings.GetMyAd)))
        {
            connection.Open();
            SqlCommand cmd = new SqlCommand("insert into Clicks(dateRequest, ip, ScriptID, LotID, Token, UserAgent) " +
                                            "values (getdate(), @ip, @ScriptID, @LotID, @Token, @UserAgent)",
                                            connection);
            cmd.Parameters.AddWithValue("@IP", ip);
            cmd.Parameters.AddWithValue("@ScriptID", ScriptID);
            cmd.Parameters.AddWithValue("@LotID", LotID);
            cmd.Parameters.AddWithValue("@Token", Token);
            cmd.Parameters.AddWithValue("@UserAgent", UserAgent);
            try
            {
                cmd.ExecuteNonQuery();
            }
            catch (Exception e1)
            {
                Common.Log(e1);
            }
            finally
            {
                if ((connection != null) && (connection.State != System.Data.ConnectionState.Closed))
                    connection.Close();
            }
        }
    }


}
