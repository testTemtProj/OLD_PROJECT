using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using MongoDB.Driver;

namespace AdvertiseShow
{
    class LotManager
    {
        public LotManager(Guid AdvertiseID, Guid MarketID, string Country)
        {
            this.AdvertiseID = AdvertiseID;
            this.MarketID = MarketID;
            this.Country = Country;
            loadRates();
        }

        public Guid AdvertiseID { get; set; }
        public Guid MarketID { get; set; }
        public string Country { get; set; }


        struct LotManagerParams
        {
            public Guid AdvertiseID;
            public Guid MarketID;
            public string Country;
        }
        
        public static LotManager GetManager(Guid AdvertiseID, Guid MarketID, string Country)
        {
            LotManagerParams parameters = new LotManagerParams()
            {
                AdvertiseID = AdvertiseID,
                MarketID = MarketID,
                Country = Country
            };
            if (managersCache_.ContainsKey(parameters))
                return managersCache_[parameters];
            
            LotManager manager = new LotManager(AdvertiseID, MarketID, Country);
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
            mutexInit.WaitOne();
            var mongo = new Mongo();
            mongo.Connect();
            var db = mongo.getDB("getmyad_db");
            var spec = new Document();
            spec["advertise"] = AdvertiseID.ToString().ToUpper();
            spec["market"] = MarketID.ToString().ToUpper();
            Document lotRatesDocument = db.GetCollection("rates.lot").FindOne(spec);
            if (lotRatesDocument == null) return;
            Document []rates = lotRatesDocument["rates"] as Document[];
            foreach (Document row in rates)
            {
                var lot = Lot.get(new Guid(row["lot"].ToString()));
                var rate = (double)row["rate"];
                if (lot != null)
                    lots_.Add(lot, rate);
            };
            mutexInit.ReleaseMutex();
        }

        private RandomEntity<Lot> lots_ = new RandomEntity<Lot>();
    }
}
