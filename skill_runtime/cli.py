from __future__ import annotations

import argparse
import json

from skill_runtime.engine import list_skills, list_workflows, run_skill, run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local content skill runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-skills", help="List available skills")
    subparsers.add_parser("list-workflows", help="List available workflows")

    run_skill_parser = subparsers.add_parser("run-skill", help="Run one skill")
    run_skill_parser.add_argument("skill_id", help="Skill ID to run")
    run_skill_parser.add_argument("--input", required=True, help="Input file path")

    run_workflow_parser = subparsers.add_parser("run-workflow", help="Run one workflow")
    run_workflow_parser.add_argument("workflow_id", help="Workflow ID to run")
    run_workflow_parser.add_argument("--input", required=True, help="Input file path")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list-skills":
      print(json.dumps(list_skills(), ensure_ascii=False, indent=2))
      return

    if args.command == "list-workflows":
      print(json.dumps(list_workflows(), ensure_ascii=False, indent=2))
      return

    if args.command == "run-skill":
      result = run_skill(args.skill_id, args.input)
      print(
          json.dumps(
              {
                  "skill_id": result.skill_id,
                  "output_path": result.output_path,
                  "metadata": result.metadata,
              },
              ensure_ascii=False,
              indent=2,
          )
      )
      return

    if args.command == "run-workflow":
      result = run_workflow(args.workflow_id, args.input)
      print(json.dumps(result, ensure_ascii=False, indent=2))
      return

    parser.error("Unknown command")


if __name__ == "__main__":
    main()
