using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Web.SessionState;

namespace YottosCatalog.Handlers {   
    public class CheckImageHandler : IHttpHandler, IRequiresSessionState {
        public void ProcessRequest(HttpContext context) {
            var secretCode = new Random().Next(10001, 99999).ToString();
            context.Session["secret_word"] = secretCode;

            var bmp = new Bitmap(95, 30);
            var graphics = Graphics.FromImage(bmp);

            graphics.Clear(Color.White);
            graphics.FillRectangle(new HatchBrush(HatchStyle.DiagonalCross, Color.DarkGray, Color.White), 0, 0, 95, 30);
            graphics.DrawString(secretCode, new Font("Arial", 18), new SolidBrush(Color.Black), new PointF(10.0F, 2.0F));

            var encoderParams = new EncoderParameters(1);
            encoderParams.Param[0] = new EncoderParameter(Encoder.Quality, 25L);
            var imageCodecInfo = (from encoder in ImageCodecInfo.GetImageEncoders()
                                  where encoder.MimeType.Equals("image/jpeg")
                                  select encoder).Single();
            context.Response.Expires = -1;
            context.Response.ContentType = "image/jpeg";
            bmp.Save(context.Response.OutputStream, imageCodecInfo, encoderParams);
        }

        public bool IsReusable { get { return false; } }
    }
}