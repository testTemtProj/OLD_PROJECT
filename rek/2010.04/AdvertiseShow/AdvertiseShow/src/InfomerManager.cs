using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Data.SqlClient;

namespace AdvertiseShow
{
    class InfomerManager
    {
        /// <summary>
        /// Возвращает следующий случайный информер
        /// </summary>
        /// <returns></returns>
        public static Lot get()
        {
            if (informers_ == null)
                load();
            return informers_.get();
        }


        public static void Clear()
        {
            informers_ = null;
        }

        private static void load()
        {
            using (var connection = new SqlConnection(Common.ConnectionString))
            {
                connection.Open();
                SqlDataReader rs = null;
                informers_ = new RandomEntity<Lot>();
                try
                {
                    var cmd = new SqlCommand("select distinct LotID from AdvertiseScriptLots where MarketID is null", connection);
                    rs = cmd.ExecuteReader();
                    while (rs.Read())
                    {
                        Lot informer = Lot.get(new Guid(rs[0].ToString()));
                        if (informer != null)
                            informers_.Add(informer, 1);
                    }
                    rs.Close();
                }
                catch
                {
                    informers_ = null;
                }
            }
        }

        private static RandomEntity<Lot> informers_ = null;
    }
}
