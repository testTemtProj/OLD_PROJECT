<%@ WebHandler Language="C#" Class="Captcha" %>

using System;
using System.Web;
using System.Drawing;
using WebControlCaptcha;

public class Captcha : IHttpHandler {
    
    public void ProcessRequest (HttpContext context) {
        //var app = context.ApplicationInstance;

        string guid = context.Request.QueryString["guid"];
        CaptchaImage ci = null;

        if (guid != "")
        {
            if (string.IsNullOrEmpty(context.Request.QueryString["s"]))
                ci = (CaptchaImage)HttpRuntime.Cache[guid];
            else
                ci = HttpContext.Current.Session[guid] as CaptchaImage;
        }

        if (ci == null)
        {
            context.Response.StatusCode = 404;
            context.ApplicationInstance.CompleteRequest();
            return;
        }

        Bitmap b = ci.RenderImage();
        b.Save(context.Response.OutputStream, System.Drawing.Imaging.ImageFormat.Jpeg);
        b.Dispose();
        context.Response.ContentType = "image/jpeg";
        context.Response.StatusCode = 200;
        context.ApplicationInstance.CompleteRequest();
    }
 
    public bool IsReusable {
        get {
            return false;
        }
    }

}