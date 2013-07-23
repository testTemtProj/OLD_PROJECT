using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace AdvertiseShow
{
    class InformerNotFound : Exception { }

    /// <summary>
    /// Представляет рекламную выгрузку (скрипт)
    /// </summary>
    class Informer
    {
        public string Title { get; set; }
        public Guid id { get; set; }
        public string Css { get; set; }
        public int ItemsCount { get; set; }
        public string Height { get; set; }
        public string Width { get; set; }
        public enum ENullAction                     // Действие, когда нет подходящей рекламы
        {
            ShowSocial,     // Показывать социальную рекламу
            ShowURL,        // Показывать URL
            ShowNothing     // Ничего не показывать (сплошной фон)
        }
        ENullAction NullAction { get; set; }
        public string NullActionUrl { get; set; }

        /// <summary>
        /// Возвращает выгрузку с кодом id
        /// </summary>
        /// <param name="id"></param>
        /// <returns></returns>
        public static Informer get(Guid id) 
        {
            if (cache_.ContainsKey(id))
                return cache_[id];
            
            Informer ad = new Informer();
            var mongo = new MongoDB.Driver.Mongo();
            try
            {
                mongo.Connect();
                var db = mongo.getDB("getmyad_db");
                var spec = new MongoDB.Driver.Document();
                spec["guid"] = id.ToString().ToUpper();
                var advertiseDoc = db.GetCollection("Advertise").FindOne(spec);
                if (advertiseDoc == null)
                    throw new InformerNotFound();
                var admaker = advertiseDoc["admaker"] as MongoDB.Driver.Document;
                var MainOptions = admaker["Main"] as MongoDB.Driver.Document;

                ad.id = id;
                ad.Css = advertiseDoc["css"].ToString();
                ad.ItemsCount = int.Parse((string)MainOptions["itemsNumber"]);
                ad.Title = advertiseDoc["title"].ToString();
                ad.NullAction = ENullAction.ShowSocial;
                ad.Height = (string)MainOptions["height"];
                ad.Width = (string)MainOptions["width"];

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

        private static System.Collections.Generic.Dictionary<Guid, Informer> cache_ = new System.Collections.Generic.Dictionary<Guid, Informer>();
    }

    
}
