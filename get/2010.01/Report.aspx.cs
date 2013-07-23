using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;

namespace GetMyAd
{
    public partial class Report : System.Web.UI.Page
    {
        protected void Page_Load(object sender, EventArgs e)
        {
            Guid currentUser;
            try
            {
                currentUser = new Guid(Session["CurrentUserID"].ToString());
            }
            catch (Exception ex)
            {
                currentUser = new Guid();
            }

            if (!Request.IsAuthenticated || currentUser == new Guid())
            {
                System.Web.Security.FormsAuthentication.RedirectToLoginPage();
                return;
            }

            DataSourceReport.SelectParameters["GetMyAdUserID"].DefaultValue = currentUser.ToString();

        }
    }
}
