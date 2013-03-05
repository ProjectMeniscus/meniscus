import os
from meniscus.ext.plugin import plug_into, import_module


personality = os.environ['DEFAULT_PERSONALITY']

print "\n\n" + personality + "\n\n"

#plug_into('/home/stev1090/PycharmProjects/ProjectMeniscus/meniscus/meniscus')
#plugin_mod = import_module('personas.worker.pairing.pairing_app')

plug_into('/home/stev1090/PycharmProjects/ProjectMeniscus/meniscus/meniscus/personas/worker/pairing')
plugin_mod = import_module('pairing_app')

application = plugin_mod.start_up()





