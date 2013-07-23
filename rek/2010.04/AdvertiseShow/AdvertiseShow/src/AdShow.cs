using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MongoDB.Driver;
using System.Data.SqlClient;
using System.Threading;

namespace AdvertiseShow
{
    public class AdShow
    {
        private List<Lot> GetLots(Guid advertiseID, string country, int count)
        {
            var lots = new List<Lot>();
            RandomEntity<Guid> markets = loadMarketRates(advertiseID);
            if (markets == null) return null;
            int iterations = 10;
            while (lots.Count < count && iterations >= 0)
            {
                iterations--;
                Guid market = markets.get();
                LotManager lotManager = LotManager.GetManager(advertiseID, market, country);
                Lot lot;
                int takes = 10;         // Количество попыток добавления товара
                do
                {
                    lot = lotManager.NextLot();
                    takes--;
                } while (takes > 0 && lots.Contains(lot));
                if (lot == null)
                    continue;
                lots.Add(lot);
            }
            return lots;
        }


        private List<Lot> GetInformers(int count)
        {
            var res = new List<Lot>();
            int iterations = 10;
            while (res.Count < count && iterations >= 0)
            {
                iterations--;
                Lot informer = InfomerManager.get();
                if (!res.Contains(informer))
                    res.Add(informer);
            }
                
            return res;
        }

        public string Show(Guid advertiseID, string country)
        {
            var advertise = Advertise.get(advertiseID);
            var lots = (country == "UA")?
                        GetLots(advertiseID, country, advertise.ItemsCount) :
                        GetInformers(advertise.ItemsCount);
            string result = @"<div id='mainContainer'>" + 
                            @"<div id=""ads"" style=""position: absolute; left:0; top: 0"">";
            foreach (Lot lot in lots)
            {
                string link = String.Format("http://getmyad.yottos.com.ua/Redirect.ashx?id={0}&adscr={1}",
                    lot.ID, advertiseID);
                result += string.Format(@"<div class=""advBlock"">" + 
	                                    @"<a class=""advHeader"" href=""{0}"" target=""_blank"">{1}</a>" +
	                                    @"<a class=""advDescription"" href=""{0}"" target=""_blank"">{2}</a>" +
	                                    @"<a class=""advCost"" href=""{0}"" target=""_blank"">{3}</a>" +
	                                    @"<a href=""{0}"" target=""_blank""><img class=""advImage"" src=""{4}"" alt=""""/></a>" +
                                        @"</div>" + "\n",
                                        link, lot.Title, lot.Description, lot.Price, lot.ImageUrl);
            }
            AddImpressions(lots, advertiseID);

            result += string.Format(@"</div>" + 
                                    @"<div id='adInfo'><a href=""http://yottos.com.ua"" target=""_blank""></a></div>" +
                                    @"<div class='nav'> <a href='p_export.aspx?scr={0}' > <b id=""leftArrow""> &gt; </b> </a> </div>" + "\n",
                                    advertiseID);
            return @"<html><head><META http-equiv=""Content-Type"" content=""text/html; charset=utf-8"">" +
                   @"<style type=""text/css"">html, body { padding: 0; margin: 0; border: 0; }</style>" +
                   @"<!--[if lte IE 6]><script type=""text/javascript"" src=""supersleight-min.js""></script><![endif]-->" + 
                   advertise.Css +
                   "</head>\n" +
                   "<body>\n" +
                   result +
                   "</body>\n" +
                   "</html>";
        }




        /// <summary>
        /// Заставляет перезагрузить все кэши
        /// </summary
        public static void Reload()
        {
            Advertise.Clear();
            LotManager.Clear();
            InfomerManager.Clear();
            Lot.Reload();
            marketsByAdvertise_.Clear();
        }



        /// <summary>
        /// Добавляет в статистику запись о просмотрах рекламного скрипта AdvertiseID
        /// </summary>
        /// <param name="lots">Список товарных предлоджений</param>
        private void AddImpressions(List<Lot> lots, Guid AdvertiseID)
        {
            using (var connection = new SqlConnection(Common.ConnectionString))
            {
                try
                {
                    connection.Open();
                    foreach (Lot lot in lots)
                    {
                        var cmd = new SqlCommand("1gb_YottosStat.dbo.s_StatisticAds_add", connection);
                        cmd.CommandType = System.Data.CommandType.StoredProcedure;
                        cmd.Parameters.AddWithValue("@IP", "127.0.0.1");
                        cmd.Parameters.AddWithValue("@ScriptID", AdvertiseID);
                        cmd.Parameters.AddWithValue("@LotID", lot.ID);
                        cmd.Parameters.AddWithValue("@Action", 0);          // Impression
                        cmd.ExecuteNonQuery();
                    }
                }
                catch { }
                finally
                {
                    if ((connection != null) && (connection.State != System.Data.ConnectionState.Closed))
                        connection.Close();
                }
            }
        }

        private Mongo mongo_ = null;
        private Database db_ = null;

        /// <summary>
        /// Подключение к MongoDB.
        /// </summary>
        /// <returns>true в случае успеха, false - в противном случае.</returns>
        private bool ConnectMongo()
        {
            try
            {
                mongo_ = new MongoDB.Driver.Mongo();
                if (!mongo_.Connect())
                    return false;
                db_ = mongo_.getDB("getmyad_db");
                return true;
            }
            catch
            {
                mongo_ = null;
                db_ = null;
                return false;
            }
        }
    

        /// <summary>
        /// Возвращает рейтинги магазинов по рекламной выгрузке AdvertiseID (при необходимости загружает их)
        /// </summary>
        /// <param name="AdvertiseID"></param>
        private RandomEntity<Guid> loadMarketRates(Guid AdvertiseID)
        {
            if (marketsByAdvertise_.ContainsKey(AdvertiseID))
                return marketsByAdvertise_[AdvertiseID];

            initMutex.WaitOne();
            var rates = new RandomEntity<Guid>();
            ConnectMongo();
            var spec = new Document();
            spec["advertise"] = AdvertiseID.ToString().ToUpper();
            Document RatesDocument = db_.GetCollection("rates.market").FindOne(spec);
            if (RatesDocument == null) return rates;
            foreach (Document row in RatesDocument["rates"] as Document[])
            {
                var market = new Guid(row["market"].ToString());
                var rate = (double)row["rate"];
                rates.Add(market, rate);
            }
            marketsByAdvertise_[AdvertiseID] = rates;
            initMutex.ReleaseMutex();
            return rates;
        }

        private static Dictionary<Guid, RandomEntity<Guid>> marketsByAdvertise_ = new Dictionary<Guid,RandomEntity<Guid>>() ;
        private static Mutex initMutex = new Mutex();
 
    }



}





