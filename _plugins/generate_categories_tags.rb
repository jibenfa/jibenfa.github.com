puts "[Jekyll Plugin] generate_categories_tags.rb loaded"
module Jekyll
  class CategoryPageGenerator < Generator
    safe true

    def generate(site)
      site.categories.each do |category, posts|
        slug = Jekyll::Utils.slugify(category)
        path = File.join("categories", slug)
        puts "Generating category page: #{path}"
        site.pages << CategoryPage.new(site, site.source, path, category)
      end

      site.tags.each do |tag, posts|
        slug = Jekyll::Utils.slugify(tag)
        path = File.join("tags", slug)
        puts "Generating tag page: #{path}"
        site.pages << TagPage.new(site, site.source, path, tag)
      end
    end
  end

  class CategoryPage < Page
    def initialize(site, base, dir, category)
      @site = site
      @base = base
      @dir  = dir
      @name = "index.html"

      self.process(@name)
      self.read_yaml(File.join(base, "_layouts"), "category.html")
      self.data["category"] = category
      self.data["title"] = "分类：#{category}"
    end
  end

  class TagPage < Page
    def initialize(site, base, dir, tag)
      @site = site
      @base = base
      @dir  = dir
      @name = "index.html"

      self.process(@name)
      self.read_yaml(File.join(base, "_layouts"), "tag.html")
      self.data["tag"] = tag
      self.data["title"] = "标签：#{tag}"
    end
  end
end
