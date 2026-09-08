// Домашнее задание 1.
// Документоориентированные базы данных на примере MongoDB
// Дисциплина: Нереляционные базы данных
//
// Запуск:
//   docker compose up -d
//   docker exec -i school-mongodb mongosh --quiet < hw1-mongodb.js

print("=== Подготовка базы данных ===");
db = db.getSiblingDB("school_db");
db.students.drop();

const insertResult = db.students.insertMany([
  { name: "Анна", age: 20, course: 1, subjects: ["математика", "физика"], GPA: 4.5 },
  { name: "Иван", age: 22, course: 3, subjects: ["информатика", "математика"], GPA: 4.2 },
  { name: "Мария", age: 19, course: 1, subjects: ["литература", "история"], GPA: 4.8 },
  { name: "Петр", age: 21, course: 2, subjects: ["физика", "химия"], GPA: 3.9 },
  { name: "Елена", age: 20, course: 2, subjects: ["биология", "химия"], GPA: 4.1 },
]);
print(`База: ${db.getName()}`);
print(`Вставлено документов: ${Object.keys(insertResult.insertedIds).length}`);

print("\n=== Задание 1. Знакомство с коллекцией ===");
print("Команда: db.students.find().pretty()");
printjson(db.students.find().toArray());
print(`Документов в коллекции: ${db.students.countDocuments()}`);

print("\n=== Задание 2. Поиск по условию ===");
print("Команда: db.students.find({course: 1})");
const firstCourse = db.students.find({ course: 1 }).toArray();
printjson(firstCourse);
print(`Найдено студентов 1 курса: ${firstCourse.length}`);

print("\n=== Задание 3. Сложный фильтр ===");
print("Команда: db.students.find({GPA: {$gt: 4.0}, age: {$lt: 21}})");
print("В методичке ожидаются Анна и Елена, но Мария тоже подходит (age 19, GPA 4.8).");
const filtered = db.students.find({ GPA: { $gt: 4.0 }, age: { $lt: 21 } }).toArray();
printjson(filtered);
print(`Найдено документов: ${filtered.length}`);

print("\n=== Задание 4. Обновление документа ===");
print("Команда: db.students.updateOne({name: \"Мария\"}, {$inc: {GPA: 0.2}})");
const updateResult = db.students.updateOne({ name: "Мария" }, { $inc: { GPA: 0.2 } });
printjson(updateResult);
print("Проверка: db.students.find({name: \"Мария\"})");
printjson(db.students.find({ name: "Мария" }).toArray());

print("\n=== Дополнительная практика ===");
print("1) insertOne — добавить нового студента");
const newStudent = db.students.insertOne({
  name: "Олег",
  age: 23,
  course: 4,
  subjects: ["информатика", "математика"],
  GPA: 4.3,
});
printjson(newStudent);

print("2) Удалить студента с самым низким GPA");
const lowest = db.students.find().sort({ GPA: 1 }).limit(1).toArray()[0];
print(`Студент с самым низким GPA: ${lowest.name} (${lowest.GPA})`);
const deleteResult = db.students.deleteOne({ _id: lowest._id });
printjson(deleteResult);

print("3) Найти всех студентов старше 20 лет");
print("Команда: db.students.find({age: {$gt: 20}})");
printjson(db.students.find({ age: { $gt: 20 } }).toArray());

print("\n=== Итоговое состояние коллекции ===");
printjson(db.students.find().sort({ name: 1 }).toArray());
print(`Документов после дополнительной практики: ${db.students.countDocuments()}`);
