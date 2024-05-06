from asyncpg import Connection, Record


class DB:
    def __init__(self, connection: Connection):
        self.connection = connection


    async def set_default_user(self, telegram_id: int, telegram_username, telegram_name: str,
                               language=1, llm=1, active=1, block=0):
        await self.connection.execute('''INSERT INTO users_llm (tel_id, name, nick, language, llm, active, block)
                                      VALUES ($1, $2, $3, $4, $5, $6, $7)''',
                                      telegram_id, telegram_name, telegram_username, language, llm, active, block)


    async def set_active_user(self, telegram_id: int, telegram_username: str, telegram_name: str):
        active = await self.connection.fetchval('SELECT active from users_llm WHERE tel_id = $1', telegram_id)
        if active is None:
            await self.set_default_user(telegram_id=telegram_id, telegram_username=telegram_username, telegram_name=telegram_name)
        else:
            await self.connection.execute('UPDATE users_llm SET active = 1 WHERE tel_id = $1', telegram_id)


    async def set_inactive_user(self, telegram_id: int):
        await self.connection.execute('UPDATE users_llm SET active = 0 WHERE tel_id = $1', telegram_id)


    async def get_llms(self) -> Record:
        return await self.connection.fetch('SELECT id, name, img, model, category FROM llm')


    async def set_llm_to_user(self, telegram_id: int, telegram_username: str, telegram_name: str, llm_id: int):
        llm = await self.connection.fetchval('SELECT llm FROM users_llm WHERE tel_id = $1', telegram_id)
        if llm is None:
            await self.set_default_user(telegram_id, telegram_username, telegram_name, llm=llm_id)
        elif llm != llm_id:
            await self.connection.execute('UPDATE users_llm SET llm = $1 WHERE tel_id = $2', llm_id, telegram_id)
        return await self.connection.fetch('SELECT id, name, img, model, category FROM llm WHERE id = $1', llm_id)


    async def get_users_llm(self, telegram_id: int) -> tuple:
        llm = await self.connection.fetchrow('''SELECT llm.id, llm.model, llm.name, llm.category, llm.img, llm.response FROM llm
                                             LEFT JOIN users_llm ON llm.id = users_llm.llm WHERE users_llm.tel_id = $1''',
                                             telegram_id)
        if llm is None:
            # default model
            return (1, 'gemini-pro', 'gemini-1.0', '🅖', 'text')

        return (llm.get("category"), llm.get('model'), llm.get('name'), llm.get('img'), llm.get('response'))


    async def select_valid_key(self, credits: float) -> str:
        return await self.connection.fetchrow('SELECT id, key FROM stability_keys WHERE credits >= $1', credits)


    async def waste_credits(self, id: int, credits: float):
        await self.connection.execute('UPDATE stability_keys SET credits = credits - $1 WHERE id = $2', credits, id)


    async def update_credits(self, id: int, credits: float):
        await self.connection.execute('UPDATE stability_keys SET credits = $1 WHERE id = $2', credits, id)


    async def add_key(self, key: str, credits: float=25):
        await self.connection.execute('INSERT INTO stability_keys (key, credits) VALUES ($1, $2)', key, credits)


    async def all_keys(self, credits=0):
        return await self.connection.fetch('SELECT id, left(key, 15), credits FROM stability_keys WHERE credits > $1', credits)