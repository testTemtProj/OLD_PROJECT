using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Services;
using System.Data;
using System.Data.SqlClient;

namespace GetMyAd
{
    /// <summary>
    /// Summary description for $codebehindclassname$
    /// </summary>
    [WebService(Namespace = "http://tempuri.org/")]
    [WebServiceBinding(ConformsTo = WsiProfiles.BasicProfile1_1)]
    public class ReportSummary : IHttpHandler
    {

        public void ProcessRequest(HttpContext context)
        {
            context.Response.ContentType = "text/plain";
            var res = GetReport(Login.CurrentUser);
            var jsonData = new
            {
                total = res.Count,
                page = "page",
                records = res.Count,
                rows = res, 
                userdata = new 
                {
                    Наименование = "ИТОГО:", 
                    Impressions = _totalImpressions,
                    RecordedClicks = _totalRecordedClicks,
                    UniqueClicks = _totalUniqueClicks,
                    CTR = String.Format("{0:0.00%}", (_totalImpressions != 0) ? _totalRecordedClicks * 1.0 / _totalImpressions : 0),
                    CTR_Unique = String.Format("{0:0.00%}", (_totalImpressions != 0) ? _totalUniqueClicks * 1.0 / _totalImpressions : 0)
                }
            };



        context.Response.Write(Newtonsoft.Json.JsonConvert.SerializeObject(jsonData));

        }

        public bool IsReusable
        {
            get
            {
                return false;
            }
        }



        private int _totalImpressions = 0;
        private int _totalRecordedClicks = 0;
        private int _totalUniqueClicks = 0;
        public List<object> GetReport(Guid user)
        {
            using (var connection = new SqlConnection(Db.ConnectionString(Db.ConnectionStrings.Stats)))
            {
                connection.Open();
                var cmd = new SqlCommand("report_GetMyAdd", connection) {CommandType = CommandType.StoredProcedure};
                cmd.Parameters.AddWithValue("@GetMyAdUserID", user);
                var rs = cmd.ExecuteReader();
                var r = new List<object>();
                int i = 1;
                _totalImpressions = 0;
                _totalRecordedClicks = 0;
                _totalUniqueClicks = 0;
                if (rs == null) return r;
                while (rs.Read())
                {
                    double ctr, ctrUnique;
                    double.TryParse(rs["CTR"].ToString(), out ctr);
                    double.TryParse(rs["CTR_Unique"].ToString(), out ctrUnique);

                    r.Add(new
                    {
                        id = i,
                        cell = new[] 
                        { 
                            rs["LotTitle"],
                            rs["Impressions"],
                            rs["RecordedClicks"],
                            rs["UniqueClicks"],
                            String.Format("{0:0.00%}", ctr),
                            String.Format("{0:0.00%}", ctrUnique)
                        }
                    });
                    i++;
                    _totalImpressions += (int) rs["Impressions"];
                    _totalRecordedClicks += (int) rs["RecordedClicks"];
                    _totalUniqueClicks += (int)rs["UniqueClicks"];
                }
                return r;
            }
        } // end GetReport()

        
    }
}
