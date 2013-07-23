Imports System.Collections.Generic
Imports System.Xml

''' <summary>
''' Контрол обеспечивает многоязычность страницы
''' </summary>
''' <remarks></remarks>
Partial Class Controls_LangInstaller
    Inherits System.Web.UI.UserControl

    ''' <summary>
    ''' Считывает ресурс со значениями определенного языка и применяет их на странице 
    ''' </summary>
    ''' <param name="pagename"></param>
    ''' <remarks></remarks>
    Protected Sub LoadResources(ByVal pagename As String)
        Dim xmlLanguages As XmlDocument = New XmlDocument()
        Try
            Dim folder As String          
            Select Case Links.Links.CurrentDomain
                Case "com.ua"
                    folder = "Ukrainian"
                Case "ru"
                    folder = "Russian"
                Case "com"
                    folder = "English"
                Case Else
                    folder = "Russian"
            End Select
            Dim xmlPath As String = String.Format("~/languages/{0}/{1}.xml", folder, pagename)
            xmlLanguages.Load(Server.MapPath(xmlPath))
        Catch ex As Exception
            xmlLanguages = Nothing
        End Try
        If Not (xmlLanguages Is Nothing) Then
            Dim xmlSections As XmlNodeList = xmlLanguages.GetElementsByTagName("controls")
            If (Not (xmlSections Is Nothing) And (xmlSections.Count = 1)) Then
                Dim xmlSection As XmlNode = xmlSections(0)
                Dim xmlItem As XmlNode = Nothing
                For i As Integer = 0 To xmlSection.ChildNodes.Count - 1
                    Try
                        xmlItem = xmlSection.ChildNodes(i)
                        If xmlItem.LocalName.EndsWith("List") Then
                            Dim contrlName As String = xmlItem.LocalName
                            If (contrlName.EndsWith("RadioButtonList")) Then
                                For itm As Integer = 0 To xmlItem.ChildNodes.Count
                                    If itm < CType(Me.NamingContainer.FindControl(contrlName), RadioButtonList).Items.Count Then
                                        CType(Me.NamingContainer.FindControl(contrlName), RadioButtonList).Items(itm).Text = xmlItem.ChildNodes(itm).InnerText
                                    End If
                                Next
                                contrlName = String.Empty
                            End If

                            If (contrlName.EndsWith("DropDownList")) Then
                                For itm As Integer = 0 To xmlItem.ChildNodes.Count
                                    If itm < CType(Me.NamingContainer.FindControl(contrlName), DropDownList).Items.Count Then
                                        CType(Me.NamingContainer.FindControl(contrlName), DropDownList).Items(itm).Text = xmlItem.ChildNodes(itm).InnerText
                                    End If
                                Next
                                contrlName = String.Empty
                            End If

                            If (contrlName.EndsWith("CheckBoxList")) Then
                                For itm As Integer = 0 To xmlItem.ChildNodes.Count
                                    If itm < CType(Me.NamingContainer.FindControl(contrlName), CheckBoxList).Items.Count Then
                                        CType(Me.NamingContainer.FindControl(contrlName), CheckBoxList).Items(itm).Text = xmlItem.ChildNodes(itm).InnerText
                                    End If
                                Next
                                contrlName = String.Empty
                            End If

                        Else
                            Dim contrlName As String = xmlItem.LocalName
                            Dim contrlText As String = xmlItem.InnerText
                            If (contrlName.EndsWith("HyperLink")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), HyperLink).Text = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("LinkButton")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), LinkButton).Text = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("Button")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), Button).Text = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("Image")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), Image).AlternateText = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("Label")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), Label).Text = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("Literal")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), Literal).Text = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("CheckBox")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), CheckBox).Text = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("RegularExpressionValidator")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), RegularExpressionValidator).ErrorMessage = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("RequiredFieldValidator")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), RequiredFieldValidator).ErrorMessage = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("RangeValidator")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), RangeValidator).ErrorMessage = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("CompareValidator")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), CompareValidator).ErrorMessage = contrlText
                                contrlName = String.Empty
                            End If
                            If (contrlName.EndsWith("CustomValidator")) Then
                                CType(Me.NamingContainer.FindControl(contrlName), CustomValidator).ErrorMessage = contrlText
                                contrlName = String.Empty
                            End If
                        End If
                    Catch ex As Exception

                    End Try
                Next i
            End If
        End If
    End Sub


    'Protected Sub Page_PreRender(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.PreRender

    '    LoadResources(GetPageName())

    'End Sub

    Protected Sub Page_Load(ByVal sender As Object, ByVal e As System.EventArgs) Handles Me.Load
        LoadResources(GetPageName())
    End Sub

    ''' <summary>
    ''' Считывает ресурс со значениями определенного языка и возвращает значение запрашиваемого параметра
    ''' </summary>
    ''' <param name="paramname"></param>
    ''' <returns></returns>
    ''' <remarks></remarks>
    Public Function GetStringResource(ByVal paramname As String) As String
        Dim xmlLanguages As XmlDocument = New XmlDocument()
        Try
            Dim lang As String = ""
            Select Case Links.Links.CurrentDomain
                Case "ru"
                    lang = "russian"
                Case "com"
                    lang = "English"
                Case "com.ua"
                    lang = "Ukrainian"
                Case Else
                    lang = "russian"
            End Select
            Dim xmlPath As String = String.Format("~/languages/{0}/{1}.xml", lang, GetPageName())
            xmlLanguages.Load(Server.MapPath(xmlPath))
        Catch ex As Exception
            xmlLanguages = Nothing
        End Try
        If Not (xmlLanguages Is Nothing) Then
            If xmlLanguages.GetElementsByTagName(paramname).Count > 0 Then
                Return xmlLanguages.GetElementsByTagName(paramname).Item(0).InnerText
            Else
                Return String.Empty
            End If
        Else
            Return String.Empty

        End If
    End Function

    ''' <summary>
    ''' Определяет путь к странице и название ресурса для применения языка к странице
    ''' </summary>
    ''' <remarks></remarks>
    Protected Function GetPageName() As String
        Dim path As String = String.Empty
        If Me.NamingContainer.ToString().EndsWith("_master") Or Me.NamingContainer.ToString().EndsWith("_ascx") Then
            path = Me.NamingContainer.ToString()
        Else
            path = Me.Page.ToString()
        End If
        If (path.IndexOf(".") > -1) Then
            path = path.Substring(path.LastIndexOf(".") + 1)
        End If
        If (path.IndexOf("_") > -1) Then
            path = path.Remove(path.LastIndexOf("_"))
        End If
        If (path.IndexOf("_") > -1) Then
            path = path.Remove(0, path.LastIndexOf("_") + 1)
        End If

        Return path
    End Function
End Class
