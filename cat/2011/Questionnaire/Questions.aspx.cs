using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using YottosCatalog.Controls;
using System.Xml.Linq;
using System.IO;
using System.Data.SqlClient;
using System.Data;
using System.Data.SqlTypes;
using System.Data.Linq;
using System.Configuration;
using YottosCatalog.Code;

namespace YottosCatalog.Questionnaire {
    public partial class Questions : MenuPage {
        protected void Page_Load(object sender, EventArgs e) {
            (Master.FindControl("questionnaireLink") as HyperLink).Visible = false;
            Master.Description = Resources.CatalogResources.QuestionsPageTitle;
            if (Session["question_answers"] != null) {
                var theQuestion = Session["question_answers"] as question;
                question.Text = theQuestion.question_txt;
                prof.Text = theQuestion.profession;
                var counter = 1;
                foreach (var theAnswer in theQuestion.answers) {
                    var ctl = answersPanel.FindControl("answer_" + counter++) as QuestionnaireAnswer;
                    ctl.Visible = true;
                    ctl.AnswerText = theAnswer.answer_txt;
                    ctl.AnswerLink = theAnswer.associated_url;
                }
            }
        }        

        protected void AdditionalAnswer_Click(object sender, EventArgs e) {
            if (answer_4.Visible == false) answer_4.Visible = true;
            else if (answer_5.Visible == false) answer_5.Visible = true;
            else if (answer_6.Visible == false) {
                answer_6.Visible = true;
                addAnswer.Visible = false;
            }
        }

        private string QuestionnaireFileName { get { return string.Format("questionnaire_{0}y.{1}m.{2}d [{3}-{4}-{5}.{6}].xml", DateTime.Now.Year, DateTime.Now.Month, DateTime.Now.Day, DateTime.Now.Hour, DateTime.Now.Minute, DateTime.Now.Second, DateTime.Now.Millisecond); } }

        protected void finish_Click(object sender, EventArgs e) {
            var answerList = new List<QuestionnaireAnswer>();
            if (!string.IsNullOrEmpty(answer_1.AnswerText)) answerList.Add(answer_1);
            if(!string.IsNullOrEmpty(answer_2.AnswerText)) answerList.Add(answer_2);
            if (!string.IsNullOrEmpty(answer_3.AnswerText)) answerList.Add(answer_3);

            if (!string.IsNullOrEmpty(answer_4.AnswerText)) answerList.Add(answer_4);
            if (!string.IsNullOrEmpty(answer_5.AnswerText)) answerList.Add(answer_5);
            if (!string.IsNullOrEmpty(answer_6.AnswerText)) answerList.Add(answer_6);

            var questionRecord = new question() { 
                profession = prof.Text,
                question_txt = question.Text
            };            
            foreach (var answerCtl in answerList) {  
                var answerRecord = new answer() { 
                    answer_txt = answerCtl.AnswerText,
                    associated_url = answerCtl.AnswerLink,
                    image_uid = Guid.NewGuid(),
                    question = questionRecord
                };
                if (answerCtl.HasAnswerImage) { 
                    answerRecord.image_type = answerCtl.AnswerImage.ContentType;
                    var imageData = new byte[answerCtl.AnswerImage.ContentLength];
                    answerCtl.AnswerImage.InputStream.Read(imageData, 0, imageData.Length);
                    answerRecord.answer_image = new Binary(imageData);
                }
                questionRecord.answers.Add(answerRecord);
            }
            Session["question_answers"] = questionRecord;
            Response.Redirect(Resources.CatalogPageUrlsMapping.QuestionnaireResult, true);
        }
    }
}