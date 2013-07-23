using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace AdvertiseShow
{
    class AdvertiseNotFound : Exception { }

    /// <summary>
    /// Представляет рекламную выгрузку (скрипт)
    /// </summary>
    class Advertise
    {
        public string Title { get; set; }
        public Guid id { get; set; }
        public string Css { get; set; }
        public int ItemsCount { get; set; }

        /// <summary>
        /// Возвращает выгрузку с кодом id
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        public static Advertise get(Guid id) 
        {
            if (cache_.ContainsKey(id))
                return cache_[id];
            
            Advertise ad = new Advertise();
            var mongo = new MongoDB.Driver.Mongo();
            try
            {
                mongo.Connect();
                var db = mongo.getDB("getmyad_db");
                var spec = new MongoDB.Driver.Document();
                spec["guid"] = id.ToString().ToUpper();
                var advertiseDoc = db.GetCollection("Advertise").FindOne(spec);
                if (advertiseDoc == null)
                    throw new AdvertiseNotFound();
                var admaker = advertiseDoc["admaker"] as MongoDB.Driver.Document;
                var MainOptions = admaker["Main"] as MongoDB.Driver.Document;

                ad.Css = advertiseDoc["css"].ToString();
                ad.ItemsCount = int.Parse((string)MainOptions["itemsNumber"]);
                ad.Title = advertiseDoc["title"].ToString();

                cache_[id] = ad;
                return ad;
            }
            finally  
            {
                mongo.Disconnect();
            }
        }


        public static void Clear()
        {
            cache_.Clear();
        }

        private static System.Collections.Generic.Dictionary<Guid, Advertise> cache_ = new System.Collections.Generic.Dictionary<Guid, Advertise>();
    }

    
}
