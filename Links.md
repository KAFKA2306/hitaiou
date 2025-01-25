


# DataCleansing

https://vagrant.booth.pm/
https://booth.pm/ja/items/6082952
https://booth.pm/en/items/6082952
https://ornamentcorpse.booth.pm/items/6082952
https://vagrant.booth.pm/items/6491162
*6082952


https://{shop_id}.booth.pm/
https://booth.pm/{language}/items/{item_id}

https://{shop_id}.booth.pm/items/{item_id}



shop_id,item_id,is_avatar
vagrant,6082952,0

https://mukumi.booth.pm/items/5813187
shop_id,item_id,avatar
mukumi,5813187,1


---

# Database

master_item
shop,item,avatar
vagrant,6082952,0
mukumi,5813187,1

master_matching
avatar,item,userid,price
5813187,6082952,aaa,1000
5813187,6082952,bbb,2000



---

# User_input

Google form
https://forms.gle/JWDXcChpWzsqpmY97

Q1 input avatar url(Must)
Q2 input item url(Must)
Q3 input your twitter_id(Must)
Q4 input your desired price(Optional)
Q5 your desired hitaiou_worker_name(Optional)

output
df
avatar_url,item_url,twitter_id_desired_price,hitaiou_worker_name

---

# DataProcessing

input 
https://docs.google.com/spreadsheets/d/1k133iin4Fu4SHqSY7qSs9CVWFPAF0PW_F30GBFWIqRg/edit?resourcekey=&gid=1261115119#gid=1261115119

columns Q1 and Q2
https://{shop_id}.booth.pm/
https://booth.pm/{language}/items/{item_id}
https://{shop_id}.booth.pm/items/{item_id}

if items/{item_id} is in Q1(avatar_url), is_avatar is 1.
if items/{item_id} is in Q2(avatar_url), is_avatar is 0.

output
df
avatar_url,item_url,twitter_id_desired_price,hitaiou_worker_name,shop_id,item_id,is_avatar


master_item
shop,item,avatar
vagrant,6082952,0
mukumi,5813187,1

Demand_ranking(sort by PotentialSales(highest first))
avatar,item,number_of_requests,median_desired_price,PotentialSales
5813187,6082952,8,1500,number_of_requests times median_desired_price

---

Users input google form
Users and hitaiou_workers can see Demand_ranking in dashboard


これを実現するコードを書いてください。

