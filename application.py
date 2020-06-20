from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps



    

#Kullanıcı Login Kontrol Decoratoru
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapın.","danger")
            return redirect(url_for("login"))    
    return decorated_function

#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username = StringField("Kullanıcı Adı")
    email = StringField("E-Mail Adresi")
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyiniz."),
        validators.EqualTo(fieldname="confirm",message="Parola uyuşmuyor!")
    ])
    confirm = PasswordField("Parola Doğrula")

#Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")



application = Flask(__name__)
application.secret_key = "ocapak"

app.config["MYSQL_HOST"] = "database-1.cshavzvw4xmc.us-east-2.rds.amazonaws.com"
app.config["MYSQL_USER"] = "admin"
app.config["MYSQL_PASSWORD"] = "onurcan514"
app.config["MYSQL_DB"] = "dbblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

@app.route("/hesapla", methods=['POST','GET'])
def hesapla():
    if request.method == 'POST':
        sayi = request.form.get('sayi') 
        id = int(sayi)
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE id = %s"
        result = cursor.execute(sorgu,(id,))
        if result > 0:
            data = cursor.fetchone()
            sonuc = data["title"]
            return sonuc
        else:
            return str("sonuc yok")
    else:
        return "Bu sayfayı görmeye yetkiniz yok!"

@app.route("/")
def index():
    
    cursor = mysql.connection.cursor()
    sorgu = "CREATE TABLE IF NOT EXISTS tasks(task_id INT AUTO_INCREMENT PRIMARY KEY,title VARCHAR(255) NOT NULL)"
    cursor.execute(sorgu)
    mysql.connection.commit()
    
    return render_template("index.html")

@app.route("/about")
def about():

    return render_template("about.html")

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()

        return render_template("articles.html",articles = articles) 
    else:
       return render_template("articles.html") 

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Kayıt Başarılı :)","success")
        

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)


@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * from users WHERE username = %s"
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
              flash("Başarılı ile giriş yaptınız :)","success")  

              session["logged_in"]= True
              session["username"]= username
              return redirect(url_for("index"))
            else:
               flash("Parola yanlış girildi.","danger")
               return redirect(url_for("login")) 
        else:
            flash("Böyle bir kullanıcı bulunmuyor.","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)
#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

#Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))    
#Makale Ekle
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarılı ile eklendi.","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form = form)  
#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id = %s and author = %s"
    result = cursor.execute(sorgu,(id,session["username"]))

    if result > 0:
        sorgu2 = "DELETE FROM articles WHERE id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))

#Makale Güncelleme
@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html",form = form) 


    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "UPDATE articles SET title = %s,content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarılı ile güncellendi.","success")
        return redirect(url_for("dashboard"))

class ArticleForm(Form):
    title = StringField("Başlık")
    content = TextAreaField("Makale İçeriği",validators=[validators.length(min=10)])

#Makale Arama
@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()

        sorgu = "SELECT * FROM articles WHERE title LIKE '%" + keyword +"%' "

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Makale bulunamadı.","danger")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)






if __name__ == "__main__":
    application.run(debug=True)