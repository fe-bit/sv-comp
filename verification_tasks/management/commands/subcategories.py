from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from benchmarks.models import Benchmark
from verification_tasks.models import VerificationTask, Status, VerificationSubcategory, VerificationSet, VerificationCategory
import csv
import os
from tqdm import tqdm
from pathlib import Path
import re


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        vsc_data = {
            "ReachSafety": [
                ("ReachSafety-Arrays", [
                    "Arrays",
                ]),
                ("ReachSafety-BitVectors", [
                    "BitVectors"
                ]),
                ("ReachSafety-ControlFlow", [
                    "ControlFlow"
                ]),
                ("ReachSafety-ECA", [
                    "ECA"
                ]),
                ("ReachSafety-Floats", [
                    "Floats"
                ]),
                ("ReachSafety-Heap", [
                    "Heap",
                    "LinkedLists"
                ]),
                ("ReachSafety-Loops", [
                    "Loops", 
                    "VerifyThis-Loops"
                ]),
                ("ReachSafety-ProductLines",  [
                    "ProductLines"
                ]),
                ("ReachSafety-Recursive", [
                    "Recursive",
                    "VerifyThis-Recursive"
                ]),
                ("ReachSafety-Sequentialized", [
                    "Sequentialized"
                ]),

                ("ReachSafety-XCSP", [
                    "XCSP"
                ]),
                ("ReachSafety-Combinations", [
                    "Combinations"
                ]),
                ("ReachSafety-Hardware", [
                    "Hardware"
                ]),
                ("ReachSafety-Hardness", [
                    "Hardness"
                ]),
                ("ReachSafety-Fuzzle", [
                    "Fuzzle"
                ]),
            ], 
            "MemSafety": [
                ("MemSafety-Arrays", [
                    "Arrays", 
                    "Heap-Termination",
                    "VerifyThis-Loops",
                    "VerifyThis-Recursive"
                ]),
                ("MemSafety-Heap", [
                    "Heap"
                ]),
                ("MemSafety-LinkedLists", [
                    "LinkedLists",
                    "Loops",
                    "ControlFlow",
                    "ControlFlow-Termination",
                    "Recursive"
                ]),
                ("MemSafety-Juliet", [
                    "Juliet"
                ]),
                ("MemSafety-MemCleanup", [
                    "Heap",
                    "Juliet",
                    "LinkedLists",
                    "VerifyThis-Loops",
                    "VerifyThis-Recursive"
                ]),
            ],
            "ConcurrencySafety": [
                ("ConcurrencySafety-Main",[
                    "Concurrency"
                ]),
                ("ConcurrencySafety-MemSafety", [
                    "Concurrency"
                ]),
                ("ConcurrencySafety-NoOverflows", [
                    "Concurrency"
                ]),
                ("NoDataRace-Main", [
                    "Concurrency"
                ])
            ],
            "NoOverflows": [
                ("NoOverflows-Main", [
                    "Arrays",
                    "BitVectors",
                    "BitVectors-Termination",
                    "ControlFlow",
                    "ControlFlow-Termination",
                    "ECA",
                    "Floats",
                    "Heap",
                    "Heap-Termination",
                    "LinkedLists",
                    "Loops",
                    "Recursive",
                    "Sequentialized",
                    "VerifyThis-Loops",
                    "VerifyThis-Recursive",
                    "XCSP",
                    "SoftwareSystems-AWS-C-Common",
                    "SoftwareSystems-DeviceDriversLinux64"
                ]),
                ("NoOverflows-Juliet", [
                    "Juliet"
                ])
            ],
            "Termination": [
                ("Termination-BitVectors", [
                    "BitVectors-Termination"
                ]),
                ("Termination-MainControlFlow", [
                    "ControlFlow-Termination"
                ]),
                ("Termination-MainHeap", [
                    "Heap-Termination"
                ]),
                ("Termination-Other", [
                    "Arrays",
                    "BitVectors",
                    "ControlFlow",
                    "ECA",
                    "Floats",
                    "Heap",
                    "Loops",
                    "ProductLines",
                    "Recursive",
                    "Sequentialized",
                    "SoftwareSystems-uthash"
                ]),
            ],
            "SoftwareSystems": [
                ("SoftwareSystems-AWS-C-Common-ReachSafety", [
                    "SoftwareSystems-AWS-C-Common"
                ]),
                ("SoftwareSystems-coreutils-MemSafety", [
                    "SoftwareSystems-coreutils"
                ]),
                ("SoftwareSystems-coreutils-NoOverflows", [
                    "SoftwareSystems-coreutils"
                ]),
                ("SoftwareSystems-BusyBox-NoOverflows", [
                    "SoftwareSystems-BusyBox"
                ]), 
                ("SoftwareSystems-DeviceDriversLinux64-ReachSafety", [
                    "SoftwareSystems-DeviceDriversLinux64"
                ]),
                ("SoftwareSystems-DeviceDriversLinux64Large-ReachSafety", [
                    "SoftwareSystems-DeviceDriversLinux64Large"
                ]),
                ("SoftwareSystems-DeviceDriversLinux64-MemSafety", [
                    "SoftwareSystems-DeviceDriversLinux64"
                ]),
                ("SoftwareSystems-Other-ReachSafety", [
                    "SoftwareSystems-coreutils",
                    "SoftwareSystems-BusyBox",
                    "SoftwareSystems-OpenBSD"
                ]),
                ("SoftwareSystems-Other-MemSafety", [
                    "SoftwareSystems-BusyBox",
                    "SoftwareSystems-OpenBSD"
                ]),
                ("SoftwareSystems-uthash-ReachSafety", [
                    "SoftwareSystems-uthash"
                ]),
                ("SoftwareSystems-uthash-MemSafety", [
                    "SoftwareSystems-uthash"
                ]),
                ("SoftwareSystems-uthash-NoOverflows", [
                    "SoftwareSystems-uthash"
                ]), 
                ("SoftwareSystems-uthash-MemCleanup", [
                    "SoftwareSystems-uthash"
                ]),
                ("SoftwareSystems-DeviceDriversLinux64-Termination", [
                    "SoftwareSystems-DeviceDriversLinux64"
                ]),
                ("SoftwareSystems-Intel-TDX-Module-ReachSafety", [
                    "SoftwareSystems-Intel-TDX-Module"
                ])
            ],
            # "ValidationCrafted": [
            #     ("CorrectnessWitnesses-Loops", [
            #         "CorrectnessWitnesses-Loops"
            #     ]),
            #     ("ViolationWitnesses-ControlFlow", [
            #         "ViolationWitnesses-ControlFlow"
            #     ])
            # ]
        }

        p = Path("sv-benchmarks/c")
        # get all files that end with .set
        files = list(p.glob("*.set"))
        print(f"Found {len(files)} .set files in {p}")
        subcategories_map = {}
        for file in tqdm(files, desc="Processing files"):
            with open(file, "r") as f:
                lines = f.readlines()
                content = [l.strip() for l in lines if not l.startswith("# ") and len(l.strip()) > 0]
                subcategories_map[file.name.removesuffix(".set")] = content
        
        for c_name, subcategories in vsc_data.items():
            category = VerificationCategory.objects.get(name=c_name)
            for subc_name, subsets in subcategories:
                subcategory, _ = VerificationSubcategory.objects.get_or_create(
                    name=subc_name,
                    category=category
                )
                for subset in subsets:
                    vc_subset, created = VerificationSet.objects.get_or_create(
                        name=subset
                    )
                    if created:
                        vc_subset.patterns = "\n".join(subcategories_map.get(subset, []))
                        vc_subset.save()
                    vc_subset.subcategories.add(subcategory)

        # ADD TO VTs
        for vt in tqdm(VerificationTask.objects.all(), desc="Processing VerificationTasks"):
            if vt.subcategories.count() > 0:
                continue
            vt_yml = vt.yml_file_path.relative_to(p).as_posix()
            found = set()
            for vc_set in VerificationSet.objects.all():
                for pattern in vc_set.patterns.splitlines():
                    # Convert the pattern to a regex
                    pattern = pattern.replace(" ", r"\s*").replace("*", ".*")
                    # check if the yaml file name matches the pattern
                    if re.match(pattern, vt_yml):
                        # print(subc, "->", vt_yml)
                        vc_subcategories: list[VerificationSubcategory] = vc_set.subcategories.all()
                        for vcs in vc_subcategories:
                            if vcs.category == vt.category:
                                # print("Found subcategory", vcs.name, "for", vt_yml)
                                if vcs not in found:
                                    found.add(vcs)
                        # Update the subcategory of the VerificationTask
            if len(found) == 0:
                print("No match for", vt_yml)
            elif len(found) >= 1:
                for subc in found:
                    vt.subcategories.add(subc)
        print("Subcategories processing completed.")


        for vt in tqdm(VerificationTask.objects.all(), desc="Double Check VerificationTasks"):
            for subc in vt.subcategories.all():
                if subc.category != vt.category:
                    print(f"VerificationTask {vt.name} has subcategory {subc.name} with category {subc.category.name}, but it should be {vt.category.name}.")
