using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using YottosCatalog.Code;

namespace YottosCatalog.Questionnaire {
    public partial class Result : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            if (Session["question_answers"] != null && string.IsNullOrEmpty(Request.QueryString["id"])) {
                var question = Session["question_answers"] as question;
                if (!string.IsNullOrEmpty(Request.QueryString["image_uid"])) {
                    var guid = new Guid(Request.QueryString["image_uid"]);
                    var theAnswer = (from _answer in question.answers
                                     where _answer.image_uid == guid
                                     select _answer).Single();
                    Response.Clear();
                    Response.Expires = -1;
                    if(theAnswer.HasImage) {
                        Response.ContentType = theAnswer.image_type;
                        Response.OutputStream.Write(theAnswer.answer_image.ToArray(), 0, theAnswer.answer_image.Length);
                    }
                    Response.End();                    
                } else if (question_List.DataSource == null) {
                    var questions = new List<question>();
                    questions.Add(question);
                    question_List.DataSource = questions;
                    question_List.DataBind();
                    (Master.FindControl("questionnaireLink") as HyperLink).Visible = false;
                    Master.Description = Resources.CatalogResources.QuestionsPageTitle;
                }
            } else if (string.IsNullOrEmpty(Request.QueryString["id"])) Response.Redirect(Resources.CatalogPageUrlsMapping.Questionnaire , true);
            else {
                var question = from _question in new YottosCatalogDataContext().questions
                               where _question.id == int.Parse(Request.QueryString["id"])
                               select _question;
                Session["question_answers"] = question.Single();
                question_List.DataSource = question;
                question_List.DataBind();
                save.Visible = edit.Visible = false;
                (Master.FindControl("questionnaireLink") as HyperLink).Visible = false;
                Master.Description = Resources.CatalogResources.QuestionsPageTitle;
                viewMessage.Visible = viewLink.Visible = true;
                viewLink.Text = Request.Url.AbsoluteUri;
                viewLink.NavigateUrl = Request.Url.AbsoluteUri;
            }
        }

        protected void save_Click(object sender, EventArgs e) {
            var database = new YottosCatalogDataContext();
            var theQuestion = Session["question_answers"] as question;
            database.questions.InsertOnSubmit(theQuestion);
            database.SubmitChanges();
            Session.Remove("question_answers");
            Response.Redirect(string.Format("~/Questionnaire/Result.aspx?id={0}", theQuestion.id), true);
        }

        protected void edit_Click(object sender, EventArgs e) {
            Response.Redirect(Resources.CatalogPageUrlsMapping.Questionnaire, true);
        }
    }
}
