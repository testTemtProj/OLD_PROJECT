using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.ComponentModel;

namespace YottosCatalog.Controls {
    public partial class QuestionnaireAnswer : UserControl {
        [Bindable(true)]
        public string AnswerCaption { get; set; }
        public string AnswerText { get { return answer.Text; } set { answer.Text = value; } }
        [Bindable(true)]
        public string AnswerErrorMessage { get; set; }
        [Bindable(true)]
        public string AnswerHint { get; set; }
        public bool IsAnswerRequired { get; set; }
        [Bindable(true)]
        public string AnswerLinkCaption { get; set; }
        public string AnswerLink { get { return answer_link.Text; } set { answer_link.Text = value; } }
        [Bindable(true)]
        public string AnswerImageCaption { get; set; }
        public HttpPostedFile AnswerImage { get { return answer_photo.PostedFile; } }
        public bool HasAnswerImage { get { return answer_photo.HasFile; } }

        protected void Page_Load(object sender, EventArgs e) {
            DataBind();
        }
    }
}