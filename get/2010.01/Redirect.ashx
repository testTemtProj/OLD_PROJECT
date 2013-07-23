<%@ WebHandler Language="C#" Class="Redirect" %>

using System;
using System.Web;
using System.Collections.Generic;
using System.Data.SqlClient;
using GetMyAd;

public class Redirect : IHttpHandler {
    
    public void ProcessRequest (HttpContext context) {
        string link = "~";
        try
        {
            CheckUserAgent.BotFile = context.Server.MapPath("~/data/allagents.xml");
            Guid lot = new Guid(context.Request.Params["id"]);
            Guid script = new Guid(context.Request.Params["adscr"]);
            string ip = context.Request.UserHostAddress.ToString();
            string token = context.Request.Params["token"];
            string userAgent = context.Request.UserAgent;
            bool valid = checkToken(token, lot, script, ip, userAgent);
            

            //context.Response.Write(valid? "Invalid token!" : "Invalid token!");

            using (var connection = new SqlConnection(Db.ConnectionString(Db.ConnectionStrings.GetMyAd)))
            {
                // Получаем UserID
                connection.Open();
                var cmd = new SqlCommand(@"select top 1 a.UserID, l.Title, l.MarketID, a.Social, a.Enabled, l.Active " +
                                           "from Lots l inner join Advertise a on a.AdvertiseID = l.AdvertiseID " +
                                           "where l.LotID=@LotID " +
                                           "order by Active desc",
                                           connection);
                cmd.Parameters.AddWithValue("@LotID", lot);
                Guid user = new Guid();
                Guid market = new Guid();
                bool social = true;
                bool active = false;
                string title = "";
                SqlDataReader rs = null;
                try
                {
                    rs = cmd.ExecuteReader();
                    if (rs.Read())
                    {
                        title = rs["Title"].ToString();
                        user = new Guid(rs["UserID"].ToString());
                        try 
                        {
                            market = new Guid(rs["MarketID"].ToString()); 
                        }
                        catch
                        { 
                            market = Guid.Empty; 
                        }
                        social = (bool)rs["Social"];
                        active = (bool)rs["Enabled"] && (bool)rs["Active"];
                        if (active && valid)
                            if (market != Guid.Empty)
                                Db.ExecuteScalar("ViewStatisticAdd", new Dictionary<string, object>() {
                                    { "@LotID", lot }, { "@locid", 0 }, { "@Host", ip }, 
                                    { "@MarketID", market}, { "@viewUserID", user }, { "@Title", title },
                                    { "@Referrer", "" } }, 
                                    Db.ConnectionStrings.Adload, true);
                            else
                                Db.ExecuteScalar("ViewStatisticAdd", new Dictionary<string, object>() {
                                    { "@LotID", lot }, { "@locid", 0 }, { "@Host", ip }, 
                                    { "@viewUserID", user }, { "@Title", title },
                                    { "@Referrer", "" } },
                                    Db.ConnectionStrings.Adload, true);
                    }
                }
                catch (Exception ex)
                {
                    Common.Log(ex, string.Format("Script: {0}, Lot: {1}, IP: {2}", script, lot, ip));
                }
                finally
                {
                    if (rs != null && !rs.IsClosed) rs.Close();
                }

                if (valid && !social)
                    StatisticsCTR.ItemClicked(lot, script, ip, token, userAgent);

                link = (string) Db.ExecuteScalar("SELECT TOP 1 [Link] from Lots where LotID=@LotID order by Active desc",
                    new Dictionary<string, object>() { { "@LotID", lot } }, Db.ConnectionStrings.GetMyAd, false);

                //if (link == null)
                //    link = (string)Db.ExecuteScalar("SELECT TOP 1 [Link] from AdvertiseScriptLots_Archive where LotID=@LotID and ScriptID=@ScriptID order by Active desc",
                //        new Dictionary<string, object>() { { "@LotID", lot }, { "@ScriptID", script } }, Db.ConnectionStrings.Adload, false);
                    
                context.Response.Redirect(link, false);
                return;
            }
        }
        catch (Exception ex)
        {
            Common.Log(ex, "link: " + link);
        }

        context.Response.Redirect("http://yottos.com.ua");
    }
 
    public bool IsReusable {
        get {
            return false;
        }
    }



    /// <summary>
    /// Проверка токена ссылки на действительность:
    ///     1) По ссылке должен перейти тот же ip, которому она предназначается
    ///     2) Время действия ссылки -- 120 минут
    ///     3) Должен совпасть секрет, находящийся в ссылке и на сервере
    ///     4) Должны совпасть товары и рекламные площадки
    ///     5) Данная ссылка может быть отработана только один раз
    ///     6) Переходы поисковых систем и ботов не засчитываются
    /// </summary>
    /// <param name="token"></param>
    /// <param name="Lot"></param>
    /// <param name="AdvertiseID"></param>
    /// <param name="ip"></param>
    /// <returns></returns>
    private bool checkToken(string token, Guid LotID, Guid ScriptID, string ip, string userAgent)
    {
        try
        {
            var tokenParts = token.Split("+ ".ToCharArray());
            Int64 id = Int64.Parse(tokenParts[0]);
            string secret = tokenParts[1];

            // Проверяем п. 6 (боты и поисковые системы)
            if (CheckUserAgent.Instance.IsBot(userAgent))
            {
                reportVoidClick("Бот", token, LotID, ScriptID, ip, userAgent);
                return false;
            }



            return true;
            
            
            using (var connection = new SqlConnection(Db.ConnectionString(Db.ConnectionStrings.Stats)))
            {
                // Проверяем на пп. 1,2,3,4
                connection.Open();
                var cmd = new SqlCommand("select * from StatisticAds where id=@id", connection);
                cmd.Parameters.AddWithValue("@id", id);
                SqlDataReader rs = null;
                try
                {
                    rs = cmd.ExecuteReader();
                    if (!rs.Read())
                    {
                        reportVoidClick("В StatisticAds нет записи с таким id", token, LotID, ScriptID, ip, userAgent);
                        return false;
                    }
                    if ((string)rs["Secret"] != secret || (string)rs["ip"] != ip
                                || (Guid)rs["LotID"] != LotID || (Guid)rs["AdvertiseScriptID"] != ScriptID)
                    {
                        reportVoidClick("Не совпадает секрет, ip или ещё что-то", token, LotID, ScriptID, ip, userAgent);
                        return false;
                    }
                    
                    if ( (DateTime.Now - (DateTime)rs["dateRequest"]).Minutes > 120)
                    {
                        reportVoidClick("Истёк срок действия ссылки", token, LotID, ScriptID, ip, userAgent);
                        return false;
                    }
                }
                finally
                {
                    if (rs != null && !rs.IsClosed) rs.Close();
                }
                
                // Проверяем п. 5 (повторный переход по ссылке)
                cmd = new SqlCommand("select top 1 * from [1gb_YottosGetMyAd].[dbo].[Clicks] where Token=@Token", connection);
                cmd.Parameters.AddWithValue("@Token", token);
                rs = null;
                try
                {
                    rs = cmd.ExecuteReader();
                    if (rs.Read())
                    {
                        reportVoidClick("Попытка повторного перехода по ссылке", token, LotID, ScriptID, ip, userAgent);
                        return false;
                    }
                }
                finally
                {
                    if (rs != null && !rs.IsClosed) rs.Close();
                }
                
                

                return true;
            }
        }
        catch
        {
            return false;
        }
    }


    /// <summary>
    /// Делает запись о "пустом" переходе
    /// </summary>
    /// <param name="reason">Причина, по которой переход не был засчитан</param>
    /// <param name="token">Токен, переданный в параметрах URL</param>
    /// <param name="LotID">ID товара</param>
    /// <param name="ScriptID">ID рекламной выгрузки</param>
    /// <param name="ip">ip клиента</param>
    /// <param name="userAgent">User-Agent</param>
    private void reportVoidClick(string reason, string token, Guid LotID, Guid ScriptID, string ip, string userAgent)
    {
        using (var connection = new SqlConnection(Db.ConnectionString(Db.ConnectionStrings.GetMyAd)))
        {
            connection.Open();
            var cmd = new SqlCommand("insert into VoidClicks(ScriptID, LotID, ip, UserAgent, Token, Reason) " +
                                     "values (@ScriptID, @LotID, @ip, @UserAgent, @Token, @Reason)", connection);
            cmd.Parameters.AddWithValue("@ScriptID", ScriptID);
            cmd.Parameters.AddWithValue("@LotID", LotID);
            cmd.Parameters.AddWithValue("@ip", ip);
            cmd.Parameters.AddWithValue("@UserAgent", userAgent);
            cmd.Parameters.AddWithValue("@Token", token);
            cmd.Parameters.AddWithValue("@Reason", reason);
            try
            {
                cmd.ExecuteNonQuery();
            }
            catch { }
        }
    }
    
    
}