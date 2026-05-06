from app.api.routes import agents, apps, artifacts, channels, confirmations, conversations, demo, feedback, interactions, memories, messages, projects, runs, skills, system, tasks, tools, workspaces

routers = [
    system.router,
    apps.router,
    workspaces.router,
    projects.router,
    agents.router,
    tasks.router,
    runs.router,
    messages.router,
    conversations.router,
    channels.router,
    interactions.router,
    feedback.router,
    memories.router,
    artifacts.router,
    confirmations.router,
    demo.router,
    skills.router,
    tools.router,
]
