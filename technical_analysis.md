
I encountered an error while trying to use the tool. This was the error: Arguments validation failed: 1 validation error for MyToolInput
argument
  Input should be a valid string [type=string_type, input_value={'Mã cổ phiếu': 'MSB'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.11/v/string_type.
 Tool Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật. accepts these inputs: Tool Name: Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật.
Tool Arguments: {'argument': {'description': 'Mã cổ phiếu.', 'type': 'str'}}
Tool Description: Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật, cung cấp các chỉ số như SMA, EMA, RSI, MACD, Bollinger Bands, và vùng hỗ trợ/kháng cự..
Moving on then. I MUST either use a tool (use one at time) OR give my best final answer not both at the same time. When responding, I must use the following format:

```
Thought: you should always think about what to do
Action: the action to take, should be one of [Công cụ tra cứu dữ liệu cổ phiếu phục vụ phân tích kĩ thuật.]
Action Input: the input to the action, dictionary enclosed in curly braces
Observation: the result of the action
```
This Thought/Action/Action Input/Result can repeat N times. Once I know the final answer, I must return the following format:

```
Thought: I now can give a great answer
Final Answer: Your final answer must be the great and the most complete as possible, it must be outcome described

```