import mongoose from 'mongoose';
const todoSchema = new mongoose.Schema({
    title: { type: String, required: true },
  priority: {type: String } });
const Todo = mongoose.model('Todo', todoSchema);
export default Todo;
// This code defines a Mongoose schema and model for a "Todo" item.