from flask import Flask, request, render_template, send_file
import fitz  # PyMuPDF
from analyse_pdf import analyse_resume_gemini
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Folders
UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["DOWNLOAD_FOLDER"] = DOWNLOAD_FOLDER


# 📄 Extract resume text
def extract_text_from_resume(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


# 📄 Generate updated resume PDF
def generate_resume_pdf(resume_text, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    text_obj = c.beginText(40, height - 40)
    text_obj.setFont("Helvetica", 10)

    for line in resume_text.split("\n"):
        text_obj.textLine(line)

    c.drawText(text_obj)
    c.save()


# 🏠 UPLOAD PAGE
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description")

        if not resume_file or not resume_file.filename.endswith(".pdf"):
            return "Please upload a valid PDF resume"

        filename = secure_filename(resume_file.filename)
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        resume_file.save(resume_path)

        # Extract resume text
        resume_text = extract_text_from_resume(resume_path)

        # 🤖 Gemini AI analysis
        analysis = analyse_resume_gemini(resume_text, job_description)

        # 👉 OPEN RESULT IN NEW PAGE
        return render_template(
            "result.html",
            score=analysis["score"],
            result=analysis["result"],
            updated_resume=analysis["updated_resume"]
        )

    return render_template("index.html")


# ⬇ DOWNLOAD UPDATED RESUME PDF
@app.route("/download", methods=["POST"])
def download_updated_resume():
    updated_resume = request.form.get("updated_resume")

    if not updated_resume:
        return "No updated resume found", 400

    pdf_path = os.path.join(app.config["DOWNLOAD_FOLDER"], "updated_resume.pdf")
    generate_resume_pdf(updated_resume, pdf_path)

    return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


