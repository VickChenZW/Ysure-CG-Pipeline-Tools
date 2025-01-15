import re

pattern_seq = re.compile(r'^(.*?)(\d{4})\..*$')
name = pattern_seq.match('Essilor_Render_v003_mian_0153.jpg').group(1)
print(name)