CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY, -- מזהה ייחודי אוטומטי
    Username NVARCHAR(50) NOT NULL UNIQUE, -- שם משתמש ייחודי
    Email NVARCHAR(100) NOT NULL UNIQUE, -- מייל ייחודי
    PasswordHash NVARCHAR(255) NOT NULL, -- סיסמה מוצפנת
    ProfilePicURL NVARCHAR(255), -- תמונת פרופיל ב-Cloudinary
    Bio NVARCHAR(500), -- תיאור קצר
    CreatedAt DATETIME DEFAULT GETDATE() -- תאריך יצירה
);


CREATE TABLE Recipes (
    RecipeID INT IDENTITY(1,1) PRIMARY KEY,
    AuthorID INT NOT NULL, -- מזהה המשתמש שפרסם
    Title NVARCHAR(100) NOT NULL,
    Description NVARCHAR(500),
    Ingredients NVARCHAR(MAX) , -- רשימת מרכיבים
    Instructions NVARCHAR(MAX) , -- הוראות הכנה
    ImageURL NVARCHAR(255), -- תמונה ב-Cloudinary
    RawIngredients NVARCHAR(MAX),  -- רשימת מרכיבים ללא כמויות
    Servings INT,
    CreatedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (AuthorID) REFERENCES Users(UserID) ON DELETE CASCADE
);


CREATE TABLE Likes (
    UserID INT NOT NULL,
    RecipeID INT NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (UserID, RecipeID),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE NO ACTION,
    FOREIGN KEY (RecipeID) REFERENCES Recipes(RecipeID) ON DELETE CASCADE
);


CREATE TABLE Favorites (
    UserID INT NOT NULL,
    RecipeID INT NOT NULL,
    CreatedAt DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (UserID, RecipeID),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE NO ACTION,
    FOREIGN KEY (RecipeID) REFERENCES Recipes(RecipeID) ON DELETE CASCADE
);

CREATE TABLE Tags (
    TagID INT IDENTITY(1,1) PRIMARY KEY,
    TagName NVARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE RecipeTags (
    RecipeID INT NOT NULL,
    TagID INT NOT NULL,
    PRIMARY KEY (RecipeID, TagID),
    FOREIGN KEY (RecipeID) REFERENCES Recipes(RecipeID) ON DELETE CASCADE,
    FOREIGN KEY (TagID) REFERENCES Tags(TagID) ON DELETE CASCADE
);



