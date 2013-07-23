using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Data.SqlClient;
using System.Threading;

namespace AdvertiseShow
{
    /// <summary>
    /// Рекламная программа
    /// </summary>
    class Advertise
    {
        public Guid ID { get; set; }
        public string Title { get; set; }
        public bool Social { get; set; }


        /// <summary>
        /// Возвращает кампанию advertiseId
        /// </summary>
        /// <param name="advertiseId"></param>
        /// <returns></returns>
        public static Advertise get(Guid advertiseId)
        {
            try
            {
                LoadAdvertiseCache();
                Advertise ad;
                return advertiseCache_.TryGetValue(advertiseId, out ad) ? ad : null;
            }
            catch
            {
                return null;
            }
        }


        /// <summary>
        /// Возвращает список всех рекламных кампаний
        /// </summary>
        /// <returns></returns>
        public static List<Advertise> list()
        {
            try
            {
                LoadAdvertiseCache();
                return advertiseCache_.Values.ToList<Advertise>();
            }
            catch
            {
                return new List<Advertise>();
            }
        }

        public static void Reload()
        {
            advertiseCache_ = null;
        }


        private static void LoadAdvertiseCache()
        {
            try
            {
                if (!cacheMutex.WaitOne()) return;
                if (advertiseCache_ != null) return;
                advertiseCache_ = new Dictionary<Guid, Advertise>();
                using (var connection = new SqlConnection(Common.ConnectionString_GetMyAd))
                {
                    connection.Open();
                    var cmd = new SqlCommand("select AdvertiseID, Title, Social from Advertise", connection);
                    var rs = cmd.ExecuteReader();
                    while (rs.Read())
                    {
                        Advertise ad = new Advertise();
                        ad.ID = new Guid(rs["AdvertiseID"].ToString());
                        ad.Title = (string) rs["Title"];
                        ad.Social = (bool) rs["Social"];
                        advertiseCache_[ad.ID] = ad;
                    }
                    rs.Close();
                }
            }
            finally
            {
                cacheMutex.ReleaseMutex();
            }
        }

        /// <summary>
        /// Загружает тарегетинг рекламных кампаний
        /// </summary>
        private static void LoadAdvertiseTargeting()
        {
            if (!targetingMutex.WaitOne()) return;
            try
            {
                using (var connection = new SqlConnection(Common.ConnectionString_GetMyAd))
                {
                    connection.Open();
                    var cmd = new SqlCommand("select AdvertiseID, GeoTargeting from AdvertiseTargeting", connection);
                    var rs = cmd.ExecuteReader();
                    advertiseTargeting_ = new Dictionary<Guid, List<string>>();
                    while (rs.Read())
                    {
                        var advertise = new Guid(rs["AdvertiseID"].ToString());
                        var country = rs["GeoTargeting"].ToString();
                        if (!advertiseTargeting_.ContainsKey(advertise))
                            advertiseTargeting_[advertise] = new List<string>();
                        advertiseTargeting_[advertise].Add(country);
                    }
                    rs.Close();
                }
            }
            finally
            {
                targetingMutex.ReleaseMutex();
            }
        }


        /// <summary>
        /// Возвращает true, если рекламная кампания действует в стране country
        /// (или распространяется на все страны)
        /// </summary>
        /// <param name="country"></param>
        /// <returns></returns>
        public bool MatchesTargeting(string country)
        {
            if (advertiseTargeting_ == null) LoadAdvertiseTargeting();

            List<string> countries;
            if (!advertiseTargeting_.TryGetValue(ID, out countries))
                return false;

            return countries.Contains(country) || countries.Contains("**");
        }

        
        private static Mutex targetingMutex = new Mutex();
        private static Mutex cacheMutex = new Mutex();
        private static Dictionary<Guid, List<string>> advertiseTargeting_ = null;
        private static Dictionary<Guid, Advertise> advertiseCache_ = null;
    }
}
