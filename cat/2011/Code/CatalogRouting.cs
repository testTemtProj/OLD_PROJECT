using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Linq;
using System.Web;

namespace YottosCatalog.Code {
    public class CatalogRouting {
        public string Path { get; set; }
        public int Lcid { get; set; }

        public Dictionary<string, string> Routes { get; set; }

        public CatalogRouting() {
            Routes = new Dictionary<string, string>();
        }         
    }
}
