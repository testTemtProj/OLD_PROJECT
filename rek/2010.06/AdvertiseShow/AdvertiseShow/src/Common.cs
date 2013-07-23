using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace AdvertiseShow
{
    class Common
    {
        public static string ConnectionString_AdLoad
        {
            get
            {
                return "Data Source=213.186.119.106;Initial Catalog=1gb_YottosAdLoad;Persist Security Info=True;User ID=web;Password=odif8duuisdofj";
            }
        }

        public static string ConnectionString_GetMyAd
        {
            get
            {
                return "Data Source=213.186.119.106;Initial Catalog=1gb_YottosGetMyAd;Persist Security Info=True;User ID=web;Password=odif8duuisdofj";
            }
        }
    }
}
