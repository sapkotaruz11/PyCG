from pycg.pycg import CallGraphGenerator
from pycg import formats
import json

# micro-benchmark/snippets/flow_sensitive/reassigned_call/main.py


entry_point = ["./micro-benchmark/snippets/flow_sensitive/reassigned_call/main.py"]
package = "./micro-benchmark/snippets/flow_sensitive/reassigned_call"

entry_point_1 = ["./micro-benchmark/snippets/flow_sensitive/multiple_class/main.py"]
package_1 = ".//micro-benchmark/snippets/flow_sensitive/multiple_class"

entry_point_3 = ["./micro-benchmark/snippets/classes/assigned_call/main.py"]
package_3 = ".//micro-benchmark/snippets/classes/assigned_call"

max_iter = -1
operation = "meta-analysis"
cg = CallGraphGenerator(entry_point_1, package_1, max_iter, operation)
cg.analyze()


defs = cg.def_manager.get_defs()


if operation == "meta-analysis":
    formatter = formats.Meta(cg)
else:
    formatter = formats.Simple(cg)

output = formatter.generate()
# print(output)
# print(json.dumps(output, default=tuple))
with open(
    "eg_ag.json",
    "w",
) as f:
    json.dump(output, f, indent=4, default=tuple)
