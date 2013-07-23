<%@ WebHandler Language="C#" Class="sendstats" %>

using System;
using System.Configuration;
using System.Data.SqlClient;
using System.IO;
using System.Web;

public class sendstats : IHttpHandler {
    private readonly string _connectionString = ConfigurationManager.ConnectionStrings["StatConnectionString"].ConnectionString;
    public void ProcessRequest (HttpContext context) {     
        context.Response.ContentType = "text/plain";        
        var referrer = context.Request.QueryString["r"];
        var location = context.Request.QueryString["p"];
        var sessionID = context.Request.QueryString["ses"];
        var userAgent = context.Request.QueryString["ua"];
        //var time = context.Request.QueryString["t"];
        var width = Convert.ToInt32(context.Request.QueryString["w"]);
        var height = Convert.ToInt32(context.Request.QueryString["h"]);
        
        var num = Convert.ToInt32(context.Request.QueryString["n"]);
        try
        {
            using (var connection = new SqlConnection(_connectionString))
            {
                connection.Open();
                var cmd =
                    new SqlCommand(
                        "insert into Stat (ip,reffer_url,location_url,yottos_id,UserAgent,Screen_w,Screen_h,depth) VALUES (@ip,@reffer,@location,@yottos_id,@UserAgent,@width,@height,@depth)",
                        connection);
                //cmd.Parameters.AddWithValue("ID", Guid.NewGuid());
                cmd.Parameters.Add(new SqlParameter("ip", context.Request.UserHostAddress));
                cmd.Parameters.Add(new SqlParameter("Reffer", referrer));
                cmd.Parameters.Add(new SqlParameter("Location", location));
                cmd.Parameters.Add(new SqlParameter("yottos_id", sessionID));
                cmd.Parameters.Add(new SqlParameter("UserAgent", userAgent));
                cmd.Parameters.Add(new SqlParameter("width", width));
                cmd.Parameters.Add(new SqlParameter("height", height));
                cmd.Parameters.Add(new SqlParameter("@depth", num));
                var myReader = cmd.ExecuteNonQuery();
                connection.Close();
            }
        }
        catch (Exception ex)
        {
            try 
            {
                File.AppendAllText("d:/www/ref_log.txt", DateTime.Now + ": ses=" + sessionID + " : r=" + referrer + " p=" + location + " ip:" + context.Request.UserHostAddress + " userAgent:" +
                    userAgent +
                    " W:" + width + " H:" + height +
                    "\n" + ex.Message + "\n");
            }
            catch
            {                
            }
        }        
        //var x = context.Request.QueryString["r"];        
        finally 
        {
            context.Response.Write("ok");    
            context.Response.End();
        }
    }
 
    public bool IsReusable {
        get {
            return false;
        }
    }

}
