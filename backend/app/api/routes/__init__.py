from app.api.routes import agents, artifacts, confirmations, feedback, interactions, memories, messages, projects, runs, skills, system, tasks, tools, workspaces

routers = [
    system.router,
    workspaces.router,
    projects.router,
    agents.router,
    tasks.router,
    runs.router,
    messages.router,
    interactions.router,
    feedback.router,
    memories.router,
    artifacts.router,
    confirmations.router,
    skills.router,
    tools.router,
]
