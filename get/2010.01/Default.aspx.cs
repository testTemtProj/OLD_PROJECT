using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;

namespace GetMyAd
{
    public partial class _Default : System.Web.UI.Page
    {
        protected void Page_Load(object sender, EventArgs e)
        {
            if (Request.IsAuthenticated && Session["CurrentUserID"] != null)
                Response.Redirect("~/Отчёт");
            else
                Response.Redirect("~/Вход");

        }
    }
}
