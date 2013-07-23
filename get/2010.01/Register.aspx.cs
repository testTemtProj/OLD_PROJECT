using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Net.Mail;

public partial class Register : System.Web.UI.Page
{
    protected void Page_Load(object sender, EventArgs e)
    {
        //AgreeCheckBox.Checked = false;
        //SubmitButton.Enabled = false;
        //AgreeCheckBox.Attributes.Add("onclick", string.Format("agreeClicked({0}, {1});", SubmitButton.ClientID, AgreeCheckBox.ClientID));
    }

    private MailMessage msg;

    protected void SubmitButton_Click(object sender, EventArgs e)
    {
        if (reqUserName.IsValid && reqEmail.IsValid && reqPhoneNumber.IsValid && reqUrl.IsValid && CaptchaControl1.IsValid)
        {
            SendManagerMail();
            SendUserMail();
            PanelMain.Visible = false;
            PanelThankYou.Visible = true;
        }
    }



    /// <summary>
    /// Отправляет заявку на регистрацию на электронную почту менеджера
    /// </summary>
    private void SendManagerMail()
    {
        try
        {
            var from = new MailAddress("support@yottos.com", "GetMyAd Registration");
            var to = new MailAddress("partner@yottos.com");
            msg = new MailMessage(from, to);
            msg.Subject = "Заявка на регистрацию в GetMyAd";
            msg.BodyEncoding = System.Text.Encoding.UTF8;
            msg.Body = string.Format(@"
Имя:      {0}
Url:      {1}
E-mail:   {2}
Phone:    {3}
Время:    {4}", UserNameText.Text, SiteUrl.Text, Email.Text, PhoneNumber.Text, DateTime.Now.ToLongDateString() + " " + DateTime.Now.ToShortTimeString());
            var thread = new System.Threading.Thread(new System.Threading.ThreadStart(SendMail));
            thread.Start();
        }
        catch (Exception ex)
        {
            Common.Log(ex);
        }
    }


    /// <summary>
    ////Отправляет уведомление о рассмотрении заявки пользователю
    /// </summary>
    private void SendUserMail()
    {
        try
        {
            var from = new MailAddress("support@yottos.com", "GetMyAd");
            var to = new MailAddress(Email.Text);
            msg = new MailMessage(from, to);
            msg.Subject = string.Format("Рекламная сеть Yottos - заявка на участие сайта {0}", SiteUrl.Text);
            msg.BodyEncoding = System.Text.Encoding.UTF8;
            msg.Body = string.Format(@"
Здравствуйте, {0}!
Спасибо за интерес к участию в партнёрской программе Yottos GetMyAd.

Мы обязательно рассмотрим Вашу заявку в течение трех дней и дадим ответ о 
возможности участия сайта yottos.com в рекламной сети Yottos GetMyAd. 
(http://getmyad.yottos.com.ua/info/terms_and_conditions). 

С уважением, 
Отдел Развития Рекламной Сети Yottos GetMyAd. 
partner@yottos.com 
тел.: +38 (050) 406 20 20.


P.S. Не отвечайте на это письмо! E-mail для связи: partner@yottos.com.
", UserNameText.Text);
            var thread = new System.Threading.Thread(new System.Threading.ThreadStart(SendMail));
            thread.Start();
        }
        catch (Exception ex)
        {
            Common.Log(ex);
        }
    }


    private void SendMail()
    {
        try
        {
            string user = "support";
            string password = "57fd8824";
            var client = new SmtpClient("yottos.com", 25);
            client.Credentials = new System.Net.NetworkCredential(user, password);
            client.Send(msg);
        }
        catch (Exception ex)
        {
            Common.Log(ex);
        }
    }
    protected void CaptchaControl1_PreRender(object sender, EventArgs e)
    {
        SubmitButton.Enabled = (AgreeCheckBox.Checked);
    }
}

