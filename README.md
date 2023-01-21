HENI data engineer trial

There is a folder for each task. Each one without the scrapy spider has a main.py file, containing the main code

Some comments regarding task #2. I was not sure if it was only about the regex, or i should
have used the regex in the python code to extract the data like in the example. Maybe i got a little too 
carried away with the task.

About the task #3. It probably uses not the most clean way (the site's ugly API, instead of sitemap crawler or just a regular links crawler)
But i was curious to find whether an api exists on that site that would allow easier crawling, found one, its hideous, using it doesnt look clean, but i thought i would go with it anyway, maybe just to show that i can dig into stuff like this.
The data containing the required media and dimensions can be really unstructured on that site, so i wasnt sure how much effort should go into trying to make the resulting data perfect. In more of a production scenario i would
try to get more understanding of the requirements and any post processing of data that we do. More on that in the code comments.
Not sure if the requirement "Output: Return a dataframe consisting of the following information" was to be taken literally and data was expected to be written into the pandas dataframe, so i just saved the output to the csv feed. Seems like the same thing.

Task #4. Not really sure what does " Describe inner join, left join, right join, full join." mean, so i kinda left it out.



