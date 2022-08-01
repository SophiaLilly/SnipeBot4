import interactions, asyncio, math
from embed.leaderboard import create_leaderboard_embed
class Leaderboard(interactions.Extension): # must have interactions.Extension or this wont work
    def __init__(self, client):
        self.client: interactions.Client = client
        self.osu = client.auth
        self.database = client.database

    @interactions.extension_command(
            name="leaderboard", 
            description="gets the snipe leaderboard for this server",
            options=[interactions.Option(
                name="sort",
                description="sort order of leaderboard: pp, held, tosnipe",
                type=interactions.OptionType.STRING,
                required=False,
            )
            ]
    )
    async def leaderboard(self, ctx: interactions.CommandContext, *args, **kwargs):
        await ctx.defer()
        if len(kwargs) == 0:
            sort = 'snipe_pp'
        else:
            if kwargs['sort'] == 'pp':
                sort = 'snipe_pp'
            elif kwargs['sort'] == 'held':
                sort = 'held_snipes'
            elif kwargs['sort'] == 'tosnipe':
                sort = 'not_sniped_back'
            else:
                await ctx.send("Invalid sort order. Valid options are: `pp`, `held`, `tosnipe`")
                return
        leaderboard = [] # The final leaderboard
        main_user_array = await self.database.get_user_from_channel(ctx.channel_id._snowflake)
        if not main_user_array:
            await ctx.send(f"Nobody is being tracked in this channel, please make sure you use the command in the correct channel")
            return
        main_user_id = main_user_array[1]
        main_user_friends = await self.database.get_user_friends(ctx.channel_id._snowflake)
        for friend in main_user_friends:
            leaderboard = await self.handle_friend_leaderboard(friend, main_user_id, leaderboard, main_user_array)
        self.sort_friend_snipes(leaderboard, sort)
        main_snipes_array = await self.database.get_main_user_snipes(main_user_id)
        main_sniped_array = await self.database.get_main_user_sniped(main_user_id)
        main_snipes = len(main_snipes_array)
        main_sniped = len(main_sniped_array)
        embed = await create_leaderboard_embed(leaderboard, main_user_array[2], main_snipes, main_sniped, sort)
        await ctx.send(embeds=embed)

    async def handle_friend_leaderboard(self, friend, main_user_id, leaderboard, main_user_array):
        friend_old_pp_array = await self.database.get_friend_leaderboard_score(friend[1])
        friend_old_pp = friend_old_pp_array[0]
        friend_snipes_array = await self.database.get_user_snipes(friend[1], main_user_id)
        friend_sniped_array = await self.database.get_user_snipes(main_user_id, friend[1])
        held_snipes_array = await self.calculate_one_way_snipes(friend_snipes_array, friend_sniped_array)
        not_sniped_back_array = await self.calculate_one_way_snipes(friend_sniped_array, friend_snipes_array)
        friend_snipes = len(friend_snipes_array)
        friend_sniped = len(friend_sniped_array)
        held_snipes = len(held_snipes_array)
        not_sniped_back = len(not_sniped_back_array)
        snipe_pp = await self.calculate_snipe_pp(main_user_id, friend_snipes, not_sniped_back, held_snipes, friend_sniped)
        await self.database.update_friend_leaderboard_score(main_user_array[0], friend[1], snipe_pp)
        leaderboard.append({'username': friend[2], 'not_sniped_back': not_sniped_back, 'held_snipes': held_snipes, 'snipe_pp': snipe_pp, 'old_pp': friend_old_pp})
        return leaderboard

    async def calculate_one_way_snipes(self, snipes, sniped):
        one_way_snipes = []
        for snipe in snipes:
            add_to_array = True
            for sniped_play in sniped:
                if snipe[1] == sniped_play[1]:
                    add_to_array = False
                    break
            if add_to_array is True:
                one_way_snipes.append(snipe)
        return one_way_snipes

    async def calculate_snipe_pp(self, main_user_id, snipes, not_sniped_back, not_sniped_main, sniped):
        """
        main_user_id - the osu! id of the main user
        snipes - the number of snipes that this user has made against the main user
        not_sniped_back - the number of snipes that this user hasnt sniped back against the main user
        not_sniped_main - the number of snipes that this user has sniped on the main user, AND the main user hasnt sniped back
        sniped - the number of snipes that this user has sniped on by the main user
        """
        multiplier = 1
        total_scores = await self.database.get_all_scores(main_user_id)
        total_scores = len(total_scores)
        if snipes < total_scores:
            multiplier = (5/100) + (0.95 * (snipes/(total_scores+1)))
        calculated_pp = round((multiplier*((3*snipes + 7*not_sniped_main)/(2*not_sniped_back+(snipes/(not_sniped_main+1))*sniped+1)*10000)), 2)
        weighted_pp = await self.weight_snipe_pp(calculated_pp)
        return weighted_pp

    async def weight_snipe_pp(self, pp):
        # PP gets harder to gain every 1000pp that you have.
        # This penalty maxes out at 5x harder to gain
        if pp <= 1000:
            return pp
        new_pp = 0
        frac = math.floor(pp/1000)
        for i in range(0, frac+1):
            if i > 4: # the weighting maxes out at 1/5 penalty
                new_pp += (1/5) * pp
                break
            elif pp < 1000:
                new_pp += (1/(i+1))*pp
            else:
                new_pp += (1/(i+1))*1000
            pp = (pp - 1000)
        return new_pp   
            

    def sort_friend_snipes(self, friends_data, sort):
        # NOT async because it's a local function
        friends_data.sort(
            reverse=True, key=lambda friends_data: friends_data[sort]
        )

def setup(client):
    Leaderboard(client)