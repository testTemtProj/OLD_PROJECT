using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MongoDB.Driver;

namespace AdvertiseShow
{
    class LotManager
    {
        public LotManager(Guid informerId, Guid advertiseId, string country)
        {
            this.informerId = informerId;
            this.advertiseId = advertiseId;
            this.country = country;
            loadRates();
        }

        public Guid informerId { get; set; }
        public Guid advertiseId { get; set; }
        public string country { get; set; }


        struct LotManagerParams
        {
            public Guid informerId;
            public Guid advertiseId;
            public string country;
        }
        
        public static LotManager GetManager(Guid informerId, Guid advertiseId, string country)
        {
            LotManagerParams parameters = new LotManagerParams()
            {
                informerId = informerId,
                advertiseId = advertiseId,
                country = country
            };
            if (managersCache_.ContainsKey(parameters))
                return managersCache_[parameters];
            
            LotManager manager = new LotManager(informerId, advertiseId, country);
            managersCache_[parameters] = manager;
            return manager;
        }

        private static Dictionary<LotManagerParams, LotManager> managersCache_ = new Dictionary<LotManagerParams, LotManager>();


        /// <summary>
        /// Возвращает следующий случайный товар
        /// </summary>
        /// <returns></returns>
        public Lot NextLot()
        {
            return lots_.get();
        }


        public static void Clear()
        {
            managersCache_.Clear();
        }

        private static System.Threading.Mutex mutexInit = new System.Threading.Mutex();

        private void loadRates()
        {
            try
            {
                mutexInit.WaitOne();
                var mongo = new Mongo();
                mongo.Connect();
                var db = mongo.getDB("getmyad_db");
                var spec = new Document();
                spec["informer"] = informerId.ToString().ToUpper();
                spec["advertise"] = advertiseId.ToString().ToUpper();
                Document lotRatesDocument = db.GetCollection("rates.lot").FindOne(spec);
                if (lotRatesDocument == null) return;
                var rates = lotRatesDocument["rates"] as Document[];
                foreach (Document row in rates)
                {
                    var lot = Lot.get(new Guid(row["lot"].ToString()));
                    var rate = (double)row["rate"];
                    if (lot != null)
                        lots_.Add(lot, rate);
                };
            }
            catch
            {
                throw;
            }
            finally
            {
                mutexInit.ReleaseMutex();
            }
        }

        private RandomEntity<Lot> lots_ = new RandomEntity<Lot>();
    }
}
