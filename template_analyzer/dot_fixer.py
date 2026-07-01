import zipfile
import shutil
import os


def fix_dot_to_docx(dot_path: str, output_path: str) -> str:
    shutil.copy(dot_path, output_path)

    with zipfile.ZipFile(output_path, "r") as zin:
        content_types = zin.read("[Content_Types].xml").decode("utf-8")

    fixed_content_types = content_types.replace(
        "wordprocessingml.template.main+xml",
        "wordprocessingml.document.main+xml",
    )

    tmp_path = output_path + ".tmp"
    with zipfile.ZipFile(output_path, "r") as zin, \
         zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = fixed_content_types.encode("utf-8")
            zout.writestr(item, data)

    os.replace(tmp_path, output_path)
    return output_path