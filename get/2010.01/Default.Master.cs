using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;

namespace GetMyAd
{
    public partial class Default : System.Web.UI.MasterPage
    {
        protected void Page_Load(object sender, EventArgs e)
        {
            CurentYearLabel.Text = DateTime.Now.Year.ToString();
            try
            {
                if (Request.IsAuthenticated && Session["CurrentUserID"] != null)
                {
                    PanelUserInfo.Visible = true;
                    UserLoggedIn.Text = (Session["CurrentUserName"] ?? "") as string;
                }
                else
                {
                    PanelUserInfo.Visible = false;
                }
            }
            catch (Exception ex)
            {
            }

        }

        protected void HeaderSearchButton_Click(object sender, EventArgs e)
        {
            Context.Response.Redirect("http://yottos.ru/Результат/" +
                Server.UrlEncode(QueryTextBox.Text), true);
        }
    }
}
