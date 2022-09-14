from pathlib import Path


def dump_fs(html, target_folder, packlist):
    html.write(
        f"""PYGBAG_FS={len(packlist)}
__import__('os').chdir(__import__('tempfile').gettempdir())
def fs_decode(fsname, o248):
    from pathlib import Path
    filename = Path.cwd() / fsname
    if not filename.is_file():
        filename.parent.mkdir(parents=True, exist_ok=True)
        print("FS:", filename)
        with open(fsname,"wb") as fs:
            for input in o248.split("\\n"):
                if not input: continue
                fs.write(bytes([ord(c) - 248 for c in input]))
"""
    )

    for topack in packlist:
        if topack == "/main.py":
            continue

        vfs_name = topack[1:].replace("-pygbag.", ".")

        src_name = target_folder / topack[1:]

        sum = str(src_name.stat().st_size)

        if topack.lower().endswith(".py"):
            html.write(
                f'''
with open("{vfs_name}","w") as fs:fs.write("""\\
{open(src_name, "r").read()}""")
'''
            )
            html.write("\n")

        else:
            html.write(f"\nfs_decode('{vfs_name}','''\n")
            c = 0
            for b in open(src_name, "rb").read():
                html.write(chr(b + 248))
                c += 1
                if c > 78:
                    html.write("\n")
                    c = 0
            html.write("''')\n")

    html.write("\ndel fs_decode, PYGBAG_FS\n")


def make_header(html, line):
    if line and line[0] == "<":
        pass  # already a script shebang
    else:
        if line.find("pythons.js") > 0:
            # found script directives after #!
            SCRIPT = line[2:].strip()
        else:
            SCRIPT = ' src="https://pygame-web.github.io/archives/0.3.0/pythons.js"'
            SCRIPT += ' data-src="vtx,fs,gui"'

        line = (
            f"""
<html>
<head>
<meta charset="utf-8">
</head>
<script {SCRIPT} type=module id="__main__"  async defer>
#<!--
""".replace(
                "\n", ""
            )
            .replace("  ", " ")
            .strip()
        )
    print(line, end="\n", file=html)


def html_embed(target_folder, packlist: list, htmlfile: str):
    print("HTML:", htmlfile)
    RUNPY = "asyncio.run(main())"
    SKIP = False
    with open(htmlfile, "w+", encoding="utf-8") as html:
        for topack in packlist:

            if topack == "/main.py":
                for lnum, line in enumerate(
                    open(target_folder / topack[1:], "r", encoding="utf-8").readlines()
                ):
                    if line.startswith("asyncio.run"):
                        RUNPY = line
                        MAX = lnum
                        break

                for lnum, line in enumerate(
                    open(target_folder / topack[1:], "r", encoding="utf-8").readlines()
                ):
                    if SKIP:
                        if line.endswith("del fs_decode, PYGBAG_FS"):
                            SKIP = False
                    if line.startswith("PYGBAG_FS="):
                        SKIP = True

                    if SKIP:
                        continue

                    # no msdos
                    line = line.rstrip("\r\n")

                    if not lnum:
                        make_header(html, line)
                        dump_fs(html, target_folder, packlist)
                        continue
                    else:
                        if lnum >= MAX:
                            break

                    print(line, end="\n", file=html)

            break

        print(
            f"""
{RUNPY}
# --></script></html>
""",
            file=html,
        )