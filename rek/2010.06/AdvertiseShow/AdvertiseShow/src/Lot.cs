using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Data.SqlClient;

namespace AdvertiseShow
{
    class Lot
    {
        public Guid ID;
        public string Title;
        public string Link;
        public string ImageUrl;
        public string Description;
        public string Price;

        public static Lot get(Guid id)
        {
            if (!loaded_)
                load();
            Lot lot;
            return lotByID_.TryGetValue(id, out lot) ? lot : null;
        }


        private static System.Threading.Mutex mutexInit = new System.Threading.Mutex();
        private static void load()
        {
            try
            {
                if (!mutexInit.WaitOne())
                    return;

                if (loaded_)
                    return;

                lotByID_.Clear();
                LotByAdvertise_.Clear();
                using (var connection = new SqlConnection(Common.ConnectionString_GetMyAd))
                {
                    connection.Open();
                    var cmd = new SqlCommand("select LotId, Title, About, ('http://rynok.yottos.com.ua/img/' + i.filename) as ImgUrl, Link, Price, AdvertiseID " +
                                            "from Lots inner join [1gb_YottosRynok].dbo.Images i " +
                                            "on (i.url = ImgURL COLLATE Cyrillic_General_CI_AS and i.width = 80 and i.height = 80) " +
                                            "where Active = '1'",
                                            connection);
                    SqlDataReader rs = null;
                    try
                    {
                        rs = cmd.ExecuteReader();
                        while (rs.Read())
                        {
                            var lot = new Lot()
                            {
                                ID = new Guid(rs["LotID"].ToString()),
                                Title = rs["Title"].ToString(),
                                Description = rs["About"].ToString(),
                                ImageUrl = rs["ImgURL"].ToString(),
                                Link = rs["Link"].ToString(),
                                Price = rs["Price"].ToString()
                            };
                            lotByID_[lot.ID] = lot;
                            try
                            {
                                LotByAdvertise_[new Guid(rs["AdvertiseID"].ToString())] = lot;
                            }
                            catch { }
                        }
                        loaded_ = true;
                    }
                    catch
                    {
                        throw;
                    }
                    finally
                    {
                        if (rs != null && !rs.IsClosed)
                            rs.Close();
                    }
                }
            }
            finally
            {
                mutexInit.ReleaseMutex();
            }
        }



        public static void Reload()
        {
            loaded_ = false;
        }

        private static bool loaded_ = false;
        private static Dictionary<Guid, Lot> lotByID_ = new Dictionary<Guid, Lot>();
        private static Dictionary<Guid, Lot> LotByAdvertise_ = new Dictionary<Guid, Lot>();

    }
}
