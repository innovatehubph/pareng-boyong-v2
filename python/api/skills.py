from python.helpers.api import ApiHandler, Input, Output, Request, Response
import dataclasses
from python.helpers import runtime, skills, projects, files


class Skills(ApiHandler):
    @classmethod
    def requires_csrf(cls) -> bool:
        return False
    
    @classmethod
    def requires_auth(cls) -> bool:
        return True
    
    async def process(self, input: Input, request: Request) -> Output:
        action = input.get("action", "")

        try:
            if action == "list":
                data = self.list_skills(input)
            elif action == "delete":
                data = self.delete_skill(input)
            else:
                raise Exception("Invalid action")

            return {
                "ok": True,
                "data": data,
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
            }

    def list_skills(self, input: Input):
        skill_list = skills.list_skills()

        # filter by project
        if project_name := (input.get("project_name") or "").strip() or None:
            project_folder = projects.get_project_folder(project_name)
            if runtime.is_development():
                project_folder = files.normalize_a0_path(project_folder)
            skill_list = [
                s for s in skill_list if files.is_in_dir(str(s.path), project_folder)
            ]

        # filter by agent profile
        if agent_profile := (input.get("agent_profile") or "").strip() or None:
            skill_list = [
                s for s in skill_list if agent_profile in s.agent_profiles
            ]

        # Convert to JSON-serializable dicts
        result = []
        for s in skill_list:
            d = dataclasses.asdict(s)
            # Convert Path objects to strings
            d['path'] = str(d['path'])
            d['skill_md_path'] = str(d['skill_md_path'])
            result.append(d)
        return result

    def delete_skill(self, input: Input):
        skill_name = (input.get("skill_name") or "").strip()
        if not skill_name:
            raise Exception("skill_name is required")
        skills.delete_skill(skill_name)
        return {"deleted": skill_name}
