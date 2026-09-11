import argparse, json
from pathlib import Path
from .mvp import FoodMVP
from .benchmark import run
from .benchmark_tasks import run_all_tasks
from .synthetic import demonstrate
from .evaluation import run_full_evaluation
from .ingest_pipeline import ManifestRecord, run_ingestion, status_without_snapshot

def _ingest_status():
    base = Path(__file__).resolve().parent.parent.parent / "data" / "manifests"
    status = {
        "experiment_id": "003_real_food_corpus",
        "data_status": "NO_ADMITTED_REAL_RECIPE_CORPUS",
        "ingestion_ready": True,
        "blocker": "No authorized, checksum-pinned raw recipe snapshot is present in this environment.",
        "manifests": {},
    }
    for name in ("research_allowed", "commercial_candidate", "ingestion_manifest", "dataset_registry"):
        p = base / f"{name}.json"
        status["manifests"][name] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    return status

def main():
    p=argparse.ArgumentParser(prog='food')
    sub=p.add_subparsers(dest='command',required=True)
    d=sub.add_parser('demo'); d.add_argument('--json',action='store_true')
    b=sub.add_parser('benchmark')
    t=sub.add_parser('tasks')
    s=sub.add_parser('synthetic-representation-demo')
    e=sub.add_parser('evaluate')
    is_=sub.add_parser('ingest-status')
    ing=sub.add_parser('ingest')
    ing.add_argument('--snapshot', required=True)
    ing.add_argument('--manifest', required=True, help='JSON file describing the authorized snapshot manifest record')
    ing.add_argument('--output-dir', default=None)
    args=p.parse_args(); db=FoodMVP()
    if args.command=='evaluate': print(json.dumps(run_full_evaluation(),indent=2))
    elif args.command=='synthetic-representation-demo':
        print(json.dumps(demonstrate(),indent=2))
    elif args.command=='tasks': print(json.dumps(run_all_tasks(),indent=2))
    elif args.command=='ingest-status': print(json.dumps(_ingest_status(),indent=2))
    elif args.command=='ingest':
        spec = json.loads(Path(args.manifest).read_text(encoding='utf-8-sig'))
        m = ManifestRecord(**spec)
        print(json.dumps(run_ingestion(args.snapshot, m, args.output_dir), indent=2))
    elif args.command=='demo':
        out=db.generate(['tomato','coconut','black cardamom','sesame','ginger','tamarind'], {'smoky':.8,'creamy':.8,'savory':.8,'citrus':.7})
        print(json.dumps(out,indent=2))
    elif args.command=='benchmark': print(json.dumps(run(),indent=2))
if __name__=='__main__': main()