using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;

namespace GetMyAd
{
    public partial class Login : System.Web.UI.Page
    {
        protected void Page_Load(object sender, EventArgs e)
        {
            Login1.Focus();
        }

        public static Guid CurrentUser 
        {
            get; private set;
        }

        protected void Login1_Authenticate(object sender, AuthenticateEventArgs e)
        {
            object res = Db.ExecuteScalar(
                "select id from GetMyAd_Users where login=@login and password=@password",
                new Dictionary<string, object>() { { "@login", Login1.UserName }, {"@password", Login1.Password}},
                Db.ConnectionStrings.Adload);
            if (res != null)
            {
                CurrentUser = res is Guid ? (Guid)res : new Guid();
                Session.Clear();
                Session.Add("CurrentUserID", CurrentUser);
                Session.Add("CurrentUserName", Login1.UserName);
                e.Authenticated = true;
            }
            else
            {
                Session.Clear();
                e.Authenticated = false;
            }
            System.Web.Security.FormsAuthentication.RedirectFromLoginPage(Login1.UserName, true);
        }
    }
}
