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

        private const bool CHECK_CLICKED = false;   // Проверять товары, по которым данный IP уже кликал
        private const bool CHECK_RELOAD = false;    // Проверять необходимость перезагрузки

        /// <summary>
        /// Возвращает HTML-код для показа на данном сайте
        /// </summary>
        /// <param name="informerId"></param>
        /// <param name="country"></param>
        /// <param name="ip"></param>
        /// <param name="location">URL страницы, на которой расположен информер</param>
        /// <param name="referral">URL страницы, с которой пользователь перешёл на сайт с информером</param>
        /// <returns></returns>
        public string Show(Guid informerId, string country, string ip, string location, string referral)
        {
//            // Баннер для ua-football.com
//            if (informerId.ToString().ToUpper() == "A863A5E7-9638-4FE1-9943-6519E725ADB3" &&
//                (DateTime.Now.Hour >= 22 || DateTime.Now.Hour < 6) )
//            {
//                return @"
//<html><head></head>
//<body>
//<a href=""http://turnir.com.ua/hokej/28042010-detrojt_prohodit_finiks"" target=""_blank"">
//<img src=""/banners/042902_Turnir_240x350.jpg"" width=""238px"" height=""348px""/>
//</a>
//</body>
//</html>
//";
//            }

            //if (UpdateNeeded())
            //    Reload();

            var informer = Informer.get(informerId);
            var lots = GetLots(informerId, country, informer.ItemsCount, ip);
            string result = @"<div id='mainContainer'>" + 
                            @"<div id=""ads"" style=""position: absolute; left:0; top: 0"">";
            var lotTokens = AddImpressions(lots, informerId, ip, location, referral);
            foreach (var item in lotTokens)
            {
                Lot lot = item.Item1;
                string token = item.Item2;
                string link = String.Format("http://getmyad.yottos.com.ua/Redirect.ashx?id={0}&adscr={1}&token={2}",
                    lot.ID, informerId, token);
                result += string.Format(@"<div class=""advBlock"">" + 
	                                    @"<a class=""advHeader"" href=""{0}"" target=""_blank"">{1}</a>" +
	                                    @"<a class=""advDescription"" href=""{0}"" target=""_blank"">{2}</a>" +
	                                    @"<a class=""advCost"" href=""{0}"" target=""_blank"">{3}</a>" +
	                                    @"<a href=""{0}"" target=""_blank""><img class=""advImage"" src=""{4}"" alt=""""/></a>" +
                                        @"</div>" + "\n",
                                        link, lot.Title, lot.Description, lot.Price, lot.ImageUrl);
            }

            result += string.Format(@"</div>" + 
                                    @"<div id='adInfo'><a href=""http://yottos.com.ua"" target=""_blank""></a></div>" +
                                    @"<div class='nav'> <a href='p_export.aspx?scr={0}' > <b id=""leftArrow""> &gt; </b> </a> </div>" + "\n",
                                    informerId);
            return @"<html><head><META http-equiv=""Content-Type"" content=""text/html; charset=utf-8"">" +
                   @"<meta name=""robots"" content=""nofollow"" />" +
                   @"<style type=""text/css"">html, body { padding: 0; margin: 0; border: 0; }</style>" +
                   @"<!--[if lte IE 6]><script type=""text/javascript"" src=""http://cdn.yottos.com/getmyad/supersleight-min.js""></script><![endif]-->" + 
                   informer.Css +
                   "</head>\n" +
                   "<body>\n" +
                   result +
                   "</body>\n" +
                   "</html>";
        }


        /// <summary>
        /// Возвращает код скрипта, которые отрисовывает iframe для вырузки informerId
        /// </summary>
        /// <param name="informerId"></param>
        /// <returns></returns>
        public string ShowScript(Guid informerId)
        {
            var informer = Informer.get(informerId);
            return string.Format(@";document.write(""<iframe src='http://rynok.yottos.com.ua/p_export.aspx?scr={0}' height='{1}' width='{2}' frameborder='0' scrolling='no'></iframe>"");",
                informer.id,
                informer.Height,
                informer.Width);
        }


        /// <summary>
        /// Заставляет перезагрузить все кэши
        /// </summary
        public static void Reload()
        {
            Informer.Clear();
            LotManager.Clear();
            Lot.Reload();
            Advertise.Reload();
            advertisesByInformerAndCountry_.Clear();
        }


        /// <summary>
        /// Возвращает список из count товаров, которые нужно показать по заданной выгрузке и стране
        /// </summary>
        /// <param name="informerId">id рекламной выгрузки</param>
        /// <param name="country">двухбувенный код страны</param>
        /// <param name="count">Кол-во товаров, которое нужно вернуть/param>
        /// <returns></returns>
        private List<Lot> GetLots(Guid informerId, string country, int count, string ip)
        {
            var lots = new List<Lot>();
            RandomEntity<Guid> advertises = LoadAdvertiseRates(informerId, country);
            if (advertises == null) return null;
            var clicked = LotsClickedByIp(ip);
            int iterations = 10;
            while (lots.Count < count && iterations >= 0)
            {
                iterations--;
                Guid advertise = advertises.get();
                LotManager lotManager = LotManager.GetManager(informerId, advertise, country);
                Lot lot;
                int takes = 10;         // Количество попыток добавления товара
                do
                {
                    lot = lotManager.NextLot();
                    takes--;
                } while (takes > 0 && (lots.Contains(lot) || clicked.Contains(lot)));
                if (lot == null)
                    continue;
                lots.Add(lot);
            }
            return lots;
        }



        /// <summary>
        /// Добавляет в статистику запись о просмотрах рекламного скрипта AdvertiseID.
        /// Возвращает список кортежей (Lot, token), где token -- уникальная строка, соответствующая
        /// данному товару (содержит id строчки в .
        /// </summary>
        /// <param name="lots">Список товарных предлоджений</param>
        private List<Tuple<Lot, string>> AddImpressions(List<Lot> lots, Guid AdvertiseID,
                                                        string ip, string location, string referral)
        {
            using (var connection = new SqlConnection(Common.ConnectionString_AdLoad))
            {
                var result = new List<Tuple<Lot, string>>();
                try
                {
                    connection.Open();
                    foreach (Lot lot in lots)
                    {
                        string secret = random.Next(int.MaxValue).ToString("X8");
                        var cmd = new SqlCommand("1gb_YottosStat.dbo.s_StatisticAds_add", connection);
                        cmd.CommandType = System.Data.CommandType.StoredProcedure;
                        cmd.Parameters.AddWithValue("@IP", ip);
                        cmd.Parameters.AddWithValue("@ScriptID", AdvertiseID);
                        cmd.Parameters.AddWithValue("@LotID", lot.ID);
                        cmd.Parameters.AddWithValue("@Action", 0);          // Impression
                        cmd.Parameters.AddWithValue("@Secret", secret);
                        cmd.Parameters.AddWithValue("@Location", location);
                        cmd.Parameters.AddWithValue("@Referral", referral);
                        var id = cmd.ExecuteScalar().ToString();
                        string token = string.Format("{0}+{1}", id, secret);
                        result.Add(Tuple.Create(lot, token));
                    }
                }
                catch { }
                finally
                {
                    if ((connection != null) && (connection.State != System.Data.ConnectionState.Closed))
                        connection.Close();
                }
                return result;
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
        /// Возвращает рейтинги кампаний по рекламной выгрузке informerId (при необходимости загружает их)
        /// </summary>
        /// <param name="informerId"></param>
        /// <param name="country"></param>
        private RandomEntity<Guid> LoadAdvertiseRates(Guid informerId, string country)
        {
            var key = Tuple.Create(informerId, country);
            if (advertisesByInformerAndCountry_.ContainsKey(key))
                return advertisesByInformerAndCountry_[key];

            try
            {
                initMutex.WaitOne();
                var rates = new RandomEntity<Guid>();
                ConnectMongo();
                var spec = new Document();
                spec["informer"] = informerId.ToString().ToUpper();
                Document RatesDocument = db_.GetCollection("rates.advertise").FindOne(spec);
                if (RatesDocument == null)
                {
                    // Рейтинги по данному информеру ещё не были просчитаны, 
                    // временно показываем общую социальную рекламу (в кеш не сохраняем)
                    foreach (var advertise in Advertise.list())
                        if (advertise.Social)
                            rates.Add(advertise.ID, 1);
                    return rates;
                }

                // Загружаем коммерческие рекламные компани
                foreach (Document row in RatesDocument["rates"] as Document[] )
                {
                    var advertiseId = new Guid(row["advertise"].ToString());
                    var rate = (double)row["rate"];
                    var advertise = Advertise.get(advertiseId);
                    if (advertise != null && !advertise.Social && advertise.MatchesTargeting(country))
                        rates.Add(advertise.ID, rate);
                }
                if (!rates.IsEmpty())
                {
                    advertisesByInformerAndCountry_[key] = rates;
                    return rates;
                }

                // Если коммерческих предложений не было, загружаем социальную рекламу
                foreach (Document row in RatesDocument["rates"] as Document[])
                {
                    var advertiseId = new Guid(row["advertise"].ToString());
                    var rate = (double)row["rate"];
                    var advertise = Advertise.get(advertiseId);
                    if (advertise != null && advertise.Social && advertise.MatchesTargeting(country))
                        rates.Add(advertise.ID, rate);
                }
                advertisesByInformerAndCountry_[key] = rates;
                return rates;
            }
            finally
            {
                initMutex.ReleaseMutex();
            }
            
        }


        /// <summary>
        /// Проверяет, произошли какие-либо изменения со времени последней перезагрузки службы
        /// </summary>
        /// <returns></returns>
        private bool UpdateNeeded()
        {
            if (!CHECK_RELOAD)
                return false;

            if (!checkReloadMutex.WaitOne(0))
                return false;
            if ((DateTime.Now - lastUpdateCheckTime).Seconds < 5)
            {
                checkReloadMutex.ReleaseMutex();
                return false;
            }

            Mongo mongo = null;
            try
            {

                mongo = MongoConnectionPool.get();
                var db = mongo.getDB("getmyad_db");
                var docs = db["Advertise"].FindAll().Sort("lastModified", IndexOrder.Descending).Limit(1)
                            .Documents.ToArray<Document>();
                var doc = docs[0];
                if (!doc.Contains("lastModified"))
                    return true;
                var lastModified = (DateTime) docs[0]["lastModified"];
                return (lastModified > restartTime);
            }
            catch
            {
                return false;
            }
            finally
            {
                lastUpdateCheckTime = DateTime.Now;
                if (mongo != null)
                    MongoConnectionPool.back(mongo);
                checkReloadMutex.ReleaseMutex();
            }
        }



        /// <summary>
        /// Возвращает список кодов товаров, по которым данный ip уже кликал
        /// </summary>
        /// <param name="ip"></param>
        /// <returns></returns>
        private HashSet<Lot> LotsClickedByIp(string ip)
        {
            var clicks = new HashSet<Lot>();
            if (!CHECK_CLICKED) return clicks;

            Mongo mongo = null;
            try
            {
                mongo = MongoConnectionPool.get();
                var db = mongo.getDB("getmyad_db");
                var spec = new Document();
                spec["ip"] = ip;
                Document ipHistory = db.GetCollection("ip_history").FindOne(spec);
                if (ipHistory == null)
                    return clicks;
                foreach (var r in ipHistory["clicks"] as Document[])
                {
                    var lotDoc = r["lot"] as Document;
                    Guid guid = new Guid((string)lotDoc["guid"]);
                    Lot lot = Lot.get(guid);
                    clicks.Add(lot);
                }
            }
            catch { }
            finally 
            {
                if (mongo != null)
                    MongoConnectionPool.back(mongo);
            }
            return clicks;
        }

        private static Dictionary<Tuple<Guid, string>, RandomEntity<Guid>> advertisesByInformerAndCountry_ = new Dictionary<Tuple<Guid, string>, RandomEntity<Guid>>();
        private static Mutex initMutex = new Mutex();
        private static Mutex checkReloadMutex = new Mutex();
        private static Random random = new Random();
        private static DateTime restartTime = DateTime.Now;                 // Время последнего перезапуска GetMyAd
        private static DateTime lastUpdateCheckTime = DateTime.Now;         // Время последней проверки на необходимость обновлений
    }
}